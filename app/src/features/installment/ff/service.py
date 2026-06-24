import base64
import binascii
from datetime import UTC, datetime, timedelta
from secrets import compare_digest
from typing import Any

from bcrypt import checkpw
from fastapi import HTTPException, status
from loguru import logger
from src.service import BaseService

from ..schemas import (
    CreateInstallmentApplicationRequest,
    CreateInstallmentApplicationResponse,
    FFProductsResponse,
    InstallmentApplicationResponse,
    WebhookAckResponse,
)
from .client import FFClient, FFClientError
from .repo import FFProvider, FFRepository, FFWebhookCredential

VALID_FF_WEBHOOK_STATUSES = {"REJECTED", "APPROVED", "ALTERNATIVE", "ISSUED"}


class FFService(BaseService):
    def __init__(self, ff_repository: FFRepository, ff_client: FFClient, app_env: str) -> None:
        self.ff_repository = ff_repository
        self.ff_client = ff_client
        self.app_env = app_env

    async def get_products(self) -> FFProductsResponse:
        provider = await self._require_provider()
        partner_id = self._required_config_value(provider, "partner_id")
        logger.info(
            "FF get_products start | base_url={base_url} partner_id={partner_id} channel={channel} resolve_ip={resolve_ip} env={env}",
            base_url=provider.base_url,
            partner_id=partner_id,
            channel=provider.config.get("channel"),
            resolve_ip=self._provider_resolve_ip(provider),
            env=self.app_env,
        )
        access_token = await self._ensure_valid_token(provider=provider)
        ff_kwargs = self._ff_request_kwargs(provider)

        try:
            payload = await self.ff_client.get_partner_info(
                access_token=access_token,
                partner_id=partner_id,
                **ff_kwargs,
            )
        except FFClientError as exc:
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                logger.warning("FF get_products got 401, re-authenticating")
                access_token = await self._authenticate_and_store_token(provider)
                payload = await self.ff_client.get_partner_info(
                    access_token=access_token,
                    partner_id=partner_id,
                    **ff_kwargs,
                )
            else:
                logger.error(
                    "FF get_products failed | status={status} detail={detail}",
                    status=exc.status_code,
                    detail=exc.detail,
                )
                raise self._map_ff_error(exc) from exc

        logger.info("FF get_products success | payload_keys={keys}", keys=sorted(payload.keys()))
        return FFProductsResponse.model_validate(payload)

    async def create_application(
        self,
        request: CreateInstallmentApplicationRequest,
    ) -> CreateInstallmentApplicationResponse:
        if request.provider_code != "FF":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only provider_code=FF is supported.",
            )

        provider = await self._require_provider()
        if not await self.ff_repository.client_request_exists(request.client_request_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"client_request_id={request.client_request_id} was not found.",
            )

        iin = self._normalize_iin(request.iin)
        phone = self._normalize_phone(request.mobile_phone)
        if iin is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid IIN: expected 12 digits.",
            )
        if phone is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid mobile_phone: expected Kazakhstan number (+7...).",
            )

        application_id = await self.ff_repository.insert_application(
            client_request_id=request.client_request_id,
            provider_id=provider.id,
            product_id=request.product_id,
            loan_type=request.loan_type,
            principal=request.principal,
            period=request.period,
            created_by=request.created_by,
            status="NEW",
        )
        reference_id = str(application_id)

        payload = self._build_apply_payload(
            provider=provider,
            iin=iin,
            phone=phone,
            request=request,
            reference_id=reference_id,
        )

        response_payload = await self._apply_with_reauth(provider=provider, payload=payload)
        application_uuid = response_payload.get("uuid")
        if not isinstance(application_uuid, str) or not application_uuid:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Freedom Finance did not return application uuid.",
            )

        redirect_url_value = response_payload.get("url")
        redirect_url = redirect_url_value if isinstance(redirect_url_value, str) else None

        await self.ff_repository.update_application_after_apply(
            application_id=application_id,
            uuid=application_uuid,
            redirect_url=redirect_url,
            status="IN_PROGRESS",
            reference_id=reference_id,
        )
        await self.ff_repository.insert_event_log(
            installment_id=application_id,
            event_type="CREATED",
            payload=response_payload,
            source="FF",
        )

        return CreateInstallmentApplicationResponse(
            id=application_id,
            uuid=application_uuid,
            reference_id=reference_id,
            status="IN_PROGRESS",
            redirect_url=redirect_url,
            provider_code="FF",
        )

    async def get_application_by_id(self, application_id: int) -> InstallmentApplicationResponse:
        application = await self.ff_repository.get_application_by_id(application_id)
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application id={application_id} was not found.",
            )
        return application

    async def poll_application(self, application_id: int) -> InstallmentApplicationResponse:
        application = await self.ff_repository.get_application_by_id(application_id)
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application id={application_id} was not found.",
            )
        if application.uuid is None or not application.uuid.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Application does not have FF uuid yet.",
            )

        provider = await self._require_provider()
        response_payload = await self._poll_with_reauth(provider=provider, application_uuid=application.uuid)
        status_value = self._extract_poll_status(response_payload)
        approved_params = self._extract_poll_approved_params(response_payload)
        product_id = self._extract_string(response_payload, "product")
        loan_type = self._extract_string(response_payload, "loan_type")
        payload_uuid = self._extract_string(response_payload, "uuid")

        await self.ff_repository.update_application_from_poll(
            application_id=application_id,
            status=status_value,
            approved_params=approved_params,
            product_id=product_id,
            loan_type=loan_type,
            uuid=payload_uuid,
        )
        await self.ff_repository.insert_event_log(
            installment_id=application_id,
            event_type="STATUS_POLL",
            payload=response_payload,
            source="FF",
        )
        updated_application = await self.ff_repository.get_application_by_id(application_id)
        if updated_application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application id={application_id} was not found after poll update.",
            )
        return updated_application

    async def handle_webhook(
        self,
        payload: dict[str, Any],
        *,
        authorization_header: str | None,
    ) -> WebhookAckResponse:
        await self._verify_webhook_auth_if_configured(authorization_header)

        status_value = self._extract_status(payload)
        uuid = self._extract_string(payload, "uuid")
        reference_id = self._extract_string(payload, "reference_id") or self._extract_string(
            payload,
            "lead_id",
        )
        approved_params = self._build_approved_params(payload)
        loan_type = self._extract_string(payload, "loan_type")
        product_id = self._extract_string(payload, "product")
        redirect_url = self._extract_string(payload, "redirect_url")

        application = await self.ff_repository.get_application_by_reference_or_uuid(
            reference_id=reference_id,
            uuid=uuid,
        )
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application was not found by reference_id/uuid.",
            )

        if application.status == status_value and application.approved_params == approved_params:
            return WebhookAckResponse(ok=True)

        try:
            await self.ff_repository.update_application_from_webhook(
                application_id=application.id,
                status=status_value,
                approved_params=approved_params,
                uuid=uuid,
                product_id=product_id,
                loan_type=loan_type,
                redirect_url=redirect_url,
            )
            await self.ff_repository.insert_event_log(
                installment_id=application.id,
                event_type="HOOK_RECEIVED",
                payload=payload,
                source="FF",
            )
        except Exception as exc:
            await self._safe_log_webhook_error(application.id, payload, exc)
            raise

        return WebhookAckResponse(ok=True)

    async def _apply_with_reauth(self, provider: FFProvider, payload: dict[str, Any]) -> dict[str, Any]:
        access_token = await self._ensure_valid_token(provider=provider)
        ff_kwargs = self._ff_request_kwargs(provider)
        try:
            return await self.ff_client.apply_goods_loan_lead(
                access_token=access_token,
                payload=payload,
                **ff_kwargs,
            )
        except FFClientError as exc:
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                refreshed_token = await self._authenticate_and_store_token(provider=provider)
                try:
                    return await self.ff_client.apply_goods_loan_lead(
                        access_token=refreshed_token,
                        payload=payload,
                        **ff_kwargs,
                    )
                except FFClientError as retry_exc:
                    raise self._map_ff_error(retry_exc) from retry_exc
            raise self._map_ff_error(exc) from exc

    async def _poll_with_reauth(self, provider: FFProvider, application_uuid: str) -> dict[str, Any]:
        access_token = await self._ensure_valid_token(provider=provider)
        ff_kwargs = self._ff_request_kwargs(provider)
        try:
            return await self.ff_client.get_goods_application_info(
                access_token=access_token,
                uuid=application_uuid,
                **ff_kwargs,
            )
        except FFClientError as exc:
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                refreshed_token = await self._authenticate_and_store_token(provider=provider)
                try:
                    return await self.ff_client.get_goods_application_info(
                        access_token=refreshed_token,
                        uuid=application_uuid,
                        **ff_kwargs,
                    )
                except FFClientError as retry_exc:
                    raise self._map_ff_error(retry_exc) from retry_exc
            raise self._map_ff_error(exc) from exc

    async def _require_provider(self) -> FFProvider:
        provider = await self.ff_repository.get_provider_by_code("FF")
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider FF is not configured.",
            )
        return provider

    async def _ensure_valid_token(self, provider: FFProvider) -> str:
        token = await self.ff_repository.get_token(provider.id)
        now = datetime.now(UTC)
        if token is not None and token.expires_at > now + timedelta(seconds=30):
            return token.access_token
        return await self._authenticate_and_store_token(provider)

    async def _authenticate_and_store_token(self, provider: FFProvider) -> str:
        credentials = await self.ff_repository.get_active_credentials(provider.id, self.app_env)
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Active FF credentials were not found for env={self.app_env}.",
            )

        logger.info(
            "FF authenticate start | base_url={base_url} username={username} resolve_ip={resolve_ip} env={env}",
            base_url=provider.base_url,
            username=credentials.username,
            resolve_ip=self._provider_resolve_ip(provider),
            env=self.app_env,
        )
        try:
            access_token, refresh_token = await self.ff_client.authenticate(
                username=credentials.username,
                password=credentials.password,
                **self._ff_request_kwargs(provider),
            )
        except FFClientError as exc:
            logger.error(
                "FF authenticate failed | status={status} detail={detail}",
                status=exc.status_code,
                detail=exc.detail,
            )
            raise self._map_ff_error(exc) from exc

        expires_at = datetime.now(UTC) + timedelta(minutes=55)
        await self.ff_repository.upsert_token(
            provider_id=provider.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        return access_token

    @staticmethod
    def _required_config_value(provider: FFProvider, key: str) -> str:
        value = provider.config.get(key)
        if isinstance(value, str) and value.strip():
            return value
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FF provider config.{key} is missing.",
        )

    @staticmethod
    def _provider_resolve_ip(provider: FFProvider) -> str | None:
        value = provider.config.get("resolve_ip")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @classmethod
    def _ff_request_kwargs(cls, provider: FFProvider) -> dict[str, str | None]:
        return {
            "base_url": provider.base_url,
            "resolve_ip": cls._provider_resolve_ip(provider),
        }

    def _build_apply_payload(
        self,
        *,
        provider: FFProvider,
        iin: str,
        phone: str,
        request: CreateInstallmentApplicationRequest,
        reference_id: str,
    ) -> dict[str, Any]:
        return {
            "iin": iin,
            "mobile_phone": phone,
            "product": request.product_id,
            "partner": self._required_config_value(provider, "partner_id"),
            "channel": self._required_config_value(provider, "channel"),
            "credit_params": {
                "period": request.period,
                "principal": float(request.principal),
                "repayment_method": request.repayment_method,
            },
            "reference_id": reference_id,
            "credit_configs": {
                "with_insurance": False,
                "is_knox": False,
            },
            "additional_information": {
                "hook_url": self._required_config_value(provider, "hook_url"),
                "failure_url": self._required_config_value(provider, "failure_url"),
                "success_url": self._required_config_value(provider, "success_url"),
            },
        }

    @staticmethod
    def _normalize_iin(iin: str | None) -> str | None:
        if iin is None:
            return None
        normalized = "".join(symbol for symbol in iin if symbol.isdigit())
        if len(normalized) != 12:
            return None
        return normalized

    @staticmethod
    def _normalize_phone(raw_phone: str | None) -> str | None:
        if raw_phone is None:
            return None
        digits = "".join(symbol for symbol in raw_phone if symbol.isdigit())
        if digits.startswith("8") and len(digits) == 11:
            digits = "7" + digits[1:]
        if len(digits) != 11 or not digits.startswith("7"):
            return None
        return f"+{digits}"

    @staticmethod
    def _map_ff_error(exc: FFClientError) -> HTTPException:
        detail = exc.detail.strip() or "Freedom Finance request failed."
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            lowered = detail.lower()
            if "временно недоступ" in lowered:
                return HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Freedom Finance service is temporarily unavailable.",
                )
            return HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=detail,
            )
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Freedom Finance authentication failed.",
            )
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )

    async def _verify_webhook_auth_if_configured(self, authorization_header: str | None) -> None:
        credentials = await self.ff_repository.get_provider_webhook_credentials(code="FF")
        if credentials is None:
            return

        username, password = self._parse_basic_authorization_header(authorization_header)
        if username is None or password is None:
            raise self._invalid_webhook_credentials_exception()

        username_ok = compare_digest(username.encode(), credentials.username.encode())
        password_ok = self._verify_webhook_password(password, credentials)
        if not (username_ok and password_ok):
            raise self._invalid_webhook_credentials_exception()

    @staticmethod
    def _extract_string(payload: dict[str, Any], key: str) -> str | None:
        value = payload.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        return None

    @staticmethod
    def _extract_status(payload: dict[str, Any]) -> str:
        raw_status = payload.get("status")
        if not isinstance(raw_status, str) or not raw_status.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Webhook payload must include status.",
            )

        status_value = raw_status.strip().upper()
        if status_value not in VALID_FF_WEBHOOK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported status: {status_value}",
            )
        return status_value

    @staticmethod
    def _extract_poll_status(payload: dict[str, Any]) -> str:
        raw_status = payload.get("status")
        if not isinstance(raw_status, str) or not raw_status.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Poll response must include status.",
            )
        return raw_status.strip().upper()

    @staticmethod
    def _extract_poll_approved_params(payload: dict[str, Any]) -> dict[str, Any] | None:
        credit_params = payload.get("credit_params")
        if isinstance(credit_params, dict):
            return dict(credit_params)
        return None

    def _build_approved_params(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        source = payload.get("approved_params")
        approved_params = dict(source) if isinstance(source, dict) else {}
        alternative_reason = self._extract_string(payload, "alternative_reason")
        if alternative_reason is not None:
            approved_params["alternative_reason"] = alternative_reason
        return approved_params or None

    @staticmethod
    def _parse_basic_authorization_header(header_value: str | None) -> tuple[str | None, str | None]:
        if header_value is None or not header_value.startswith("Basic "):
            return None, None

        token = header_value[6:].strip()
        if not token:
            return None, None

        try:
            decoded = base64.b64decode(token, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return None, None

        if ":" not in decoded:
            return None, None
        username, password = decoded.split(":", 1)
        return username, password

    @staticmethod
    def _verify_webhook_password(password: str, credentials: FFWebhookCredential) -> bool:
        try:
            return checkpw(password.encode(), credentials.password_hash.encode())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid webhook password hash configuration.",
            ) from exc

    async def _safe_log_webhook_error(
        self,
        application_id: int,
        payload: dict[str, Any],
        exc: Exception,
    ) -> None:
        error_message = self._extract_error_message(exc)
        error_payload = {"error": error_message, "hook_payload": payload}
        try:
            await self.ff_repository.insert_event_log(
                installment_id=application_id,
                event_type="ERROR",
                payload=error_payload,
                source="FF",
            )
        except Exception:
            return

    @staticmethod
    def _extract_error_message(exc: Exception) -> str:
        if isinstance(exc, HTTPException):
            return str(exc.detail)
        return str(exc)

    @staticmethod
    def _invalid_webhook_credentials_exception() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
