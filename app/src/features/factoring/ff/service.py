import base64
import binascii
from datetime import UTC, datetime, timedelta
from pathlib import Path
from secrets import compare_digest, token_hex
from tempfile import gettempdir
from typing import Any

from bcrypt import checkpw
from fastapi import HTTPException, status
from loguru import logger
from src.service import BaseService

from ..schemas import (
    CreateFactoringApplicationRequest,
    CreateFactoringApplicationResponse,
    FactoringApplicationResponse,
    FactoringSignDocument,
    PrepareFactoringDocumentsRequest,
    PrepareFactoringDocumentsResponse,
    PrintFormItem,
    SubmitFactoringApplicationRequest,
    WebhookAckResponse,
)
from .client import FactoringClient, FactoringClientError
from .docx_fill import fill_docx_bytes
from .mynca import MyncaClient, MyncaClientError
from .repo import (
    PROVIDER_CODE,
    FactoringProvider,
    FactoringRepository,
    FactoringWebhookCredential,
)
from .templates import PRINT_FORM_SPECS, fetch_template_bytes

VALID_WEBHOOK_STATUSES = {"REJECTED", "APPROVED", "ALTERNATIVE", "ISSUED", "PENDING", "IN_PROGRESS"}
SIGNED_MYNCA_STATUSES = {"SUCCESS", "SIGNED", "COMPLETED", "DONE"}
PRINT_FORMS_CACHE_DIR = Path(gettempdir()) / "factoring-print-forms"


class FactoringService(BaseService):
    def __init__(
        self,
        repository: FactoringRepository,
        client: FactoringClient,
        app_env: str,
        mynca: MyncaClient | None = None,
        office_public_url: str = "https://office.smartremont.kz",
        public_base_url: str = "https://devintegration.smart-remont.kz",
    ) -> None:
        self.repository = repository
        self.client = client
        self.app_env = app_env
        self.mynca = mynca
        self.office_public_url = office_public_url.rstrip("/")
        self.public_base_url = public_base_url.rstrip("/")

    async def create_application(
        self,
        request: CreateFactoringApplicationRequest,
    ) -> CreateFactoringApplicationResponse:
        provider = await self._require_provider()
        if not await self.repository.client_request_exists(request.client_request_id):
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

        product_id = request.product_id or self._required_config_value(provider, "default_product_id")
        partner = self._required_config_value(provider, "partner_id")
        channel = self._required_config_value(provider, "channel")
        hook_url = self._required_config_value(provider, "hook_url")
        success_url = self._required_config_value(provider, "success_url")
        failure_url = self._required_config_value(provider, "failure_url")
        branch_code = (request.branch_code or "200000").strip()
        credit_contract = (request.credit_contract or "").strip() or self._generate_credit_contract(
            branch_code=branch_code,
            client_request_id=request.client_request_id,
        )

        print_forms = [item.model_dump(mode="json") for item in request.print_forms]
        credit_goods = (
            [item.model_dump(mode="json", exclude_none=True) for item in request.credit_goods]
            if request.credit_goods
            else None
        )

        application_id = await self.repository.insert_application(
            client_request_id=request.client_request_id,
            provider_id=provider.id,
            credit_contract=credit_contract,
            product_id=product_id,
            principal=request.principal,
            period=request.period,
            created_by=request.created_by,
            partner=partner,
            channel=channel,
            branch_code=branch_code,
            prepayment_amount=request.prepayment_amount,
            interest_rate=request.interest_rate,
            print_forms=print_forms,
            credit_goods=credit_goods,
            success_url=success_url,
            failure_url=failure_url,
            hook_url=hook_url,
            status="NEW",
        )
        reference_id = str(application_id)

        await self._log_event(
            "APPLICATION_INIT",
            factoring_id=application_id,
            source="FACTORING",
            payload={
                "client_request_id": request.client_request_id,
                "credit_contract": credit_contract,
                "product_id": product_id,
                "principal": str(request.principal),
                "period": request.period,
                "created_by": request.created_by,
                "reference_id": reference_id,
            },
        )

        bank_payload = self._build_apply_payload(
            provider=provider,
            iin=iin,
            phone=phone,
            product_id=product_id,
            partner=partner,
            channel=channel,
            credit_contract=credit_contract,
            request=request,
            print_forms=print_forms,
            credit_goods=credit_goods,
            reference_id=reference_id,
            hook_url=hook_url,
            success_url=success_url,
            failure_url=failure_url,
        )
        await self._log_event(
            "FF_APPLY_REQUEST",
            factoring_id=application_id,
            source="FF_FACTORING",
            payload=bank_payload,
        )

        try:
            response_payload = await self._apply_with_reauth(provider=provider, payload=bank_payload)
        except HTTPException as exc:
            await self._log_event(
                "FF_APPLY_FAILED",
                factoring_id=application_id,
                source="FF_FACTORING",
                payload={"error": self._extract_error_message(exc), "request": bank_payload},
            )
            raise

        application_uuid = response_payload.get("uuid")
        if not isinstance(application_uuid, str) or not application_uuid:
            await self._log_event(
                "FF_APPLY_FAILED",
                factoring_id=application_id,
                source="FF_FACTORING",
                payload={
                    "error": "Freedom Factoring did not return application uuid.",
                    "response": response_payload,
                    "request": bank_payload,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Freedom Factoring did not return application uuid.",
            )

        redirect_url = self._extract_redirect_url(response_payload)

        await self.repository.update_application_after_apply(
            application_id=application_id,
            uuid=application_uuid,
            redirect_url=redirect_url,
            status="IN_PROGRESS",
            reference_id=reference_id,
        )
        await self._log_event(
            "CREATED",
            factoring_id=application_id,
            source="FF_FACTORING",
            payload={
                "response": response_payload,
                "request": bank_payload,
                "status": "IN_PROGRESS",
            },
        )

        return CreateFactoringApplicationResponse(
            id=application_id,
            uuid=application_uuid,
            reference_id=reference_id,
            credit_contract=credit_contract,
            status="IN_PROGRESS",
            redirect_url=redirect_url,
            provider_code=PROVIDER_CODE,
        )

    async def prepare_documents(
        self,
        request: PrepareFactoringDocumentsRequest,
    ) -> PrepareFactoringDocumentsResponse:
        self._require_mynca().require_configured()
        provider = await self._require_provider()
        if not await self.repository.client_request_exists(request.client_request_id):
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

        product_id = request.product_id or self._required_config_value(provider, "default_product_id")
        partner = self._required_config_value(provider, "partner_id")
        channel = self._required_config_value(provider, "channel")
        hook_url = self._required_config_value(provider, "hook_url")
        success_url = self._required_config_value(provider, "success_url")
        failure_url = self._required_config_value(provider, "failure_url")
        branch_code = (request.branch_code or "200000").strip()
        existing = await self.repository.get_applications_by_client_request(
            request.client_request_id
        )
        credit_contract = self._generate_credit_contract(
            branch_code=branch_code,
            client_request_id=request.client_request_id,
            sequence=len(existing) + 1,
        )
        placeholders = self._template_values(
            client_fio=(request.client_fio or "").strip(),
            iin=iin,
            phone=phone,
            principal=request.principal,
            period=request.period,
            credit_contract=credit_contract,
        )
        print_forms: list[dict[str, Any]] = []
        for spec in PRINT_FORM_SPECS:
            print_forms.append(
                await self._prepare_one_print_form(
                    spec=spec,
                    placeholders=placeholders,
                    client_request_id=request.client_request_id,
                )
            )

        credit_goods = (
            [item.model_dump(mode="json", exclude_none=True) for item in request.credit_goods]
            if request.credit_goods
            else None
        )
        application_id = await self.repository.insert_application(
            client_request_id=request.client_request_id,
            provider_id=provider.id,
            credit_contract=credit_contract,
            product_id=product_id,
            principal=request.principal,
            period=request.period,
            created_by=request.created_by,
            partner=partner,
            channel=channel,
            branch_code=branch_code,
            prepayment_amount=request.prepayment_amount,
            interest_rate=request.interest_rate,
            print_forms=print_forms,
            credit_goods=credit_goods,
            success_url=success_url,
            failure_url=failure_url,
            hook_url=hook_url,
            status="WAITING_SIGN",
        )
        await self._log_event(
            "DOCUMENTS_PREPARED",
            factoring_id=application_id,
            source="FACTORING",
            payload={
                "credit_contract": credit_contract,
                "print_forms": [
                    {
                        "name": item["name"],
                        "sign_process_id": item.get("sign_process_id"),
                    }
                    for item in print_forms
                ],
            },
        )
        documents = [
            self._to_sign_document(item, application_id=application_id) for item in print_forms
        ]
        return PrepareFactoringDocumentsResponse(
            id=application_id,
            credit_contract=credit_contract,
            status="WAITING_SIGN",
            provider_code=PROVIDER_CODE,
            documents=documents,
        )

    async def refresh_sign_status(
        self,
        application_id: int,
    ) -> PrepareFactoringDocumentsResponse:
        application = await self.get_application_by_id(application_id)
        documents = await self._poll_print_form_signatures(application)
        return PrepareFactoringDocumentsResponse(
            id=application.id,
            credit_contract=application.credit_contract,
            status=application.status,
            provider_code=application.provider_code,
            documents=documents,
        )

    async def submit_application(
        self,
        application_id: int,
        request: SubmitFactoringApplicationRequest,
    ) -> CreateFactoringApplicationResponse:
        application = await self.get_application_by_id(application_id)
        if application.status not in {"WAITING_SIGN", "NEW"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Application status {application.status} cannot be submitted to the bank.",
            )
        documents = await self._poll_print_form_signatures(application)
        unsigned = [item.title for item in documents if not item.signed]
        if unsigned:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Клиент ещё не подписал: " + ", ".join(unsigned),
            )

        iin = self._normalize_iin(request.iin)
        phone = self._normalize_phone(request.mobile_phone)
        if iin is None or phone is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid IIN or mobile_phone.",
            )

        provider = await self._require_provider()
        product_id = application.product_id or self._required_config_value(
            provider, "default_product_id"
        )
        partner = application.partner or self._required_config_value(provider, "partner_id")
        channel = application.channel or self._required_config_value(provider, "channel")
        hook_url = self._required_config_value(provider, "hook_url")
        success_url = self._required_config_value(provider, "success_url")
        failure_url = self._required_config_value(provider, "failure_url")
        bank_print_forms = [
            {"name": item.name, "url": item.url}
            for item in documents
            if item.url
        ]
        apply_request = CreateFactoringApplicationRequest(
            client_request_id=application.client_request_id,
            iin=iin,
            mobile_phone=phone,
            principal=application.principal or 0,
            period=application.period or 0,
            created_by=application.created_by or 0,
            print_forms=[PrintFormItem(name=item["name"], url=item["url"]) for item in bank_print_forms],
            credit_contract=application.credit_contract,
            branch_code=application.branch_code or "200000",
            product_id=product_id,
            is_knox=request.is_knox,
        )
        reference_id = str(application.id)
        bank_payload = self._build_apply_payload(
            provider=provider,
            iin=iin,
            phone=phone,
            product_id=product_id,
            partner=partner,
            channel=channel,
            credit_contract=application.credit_contract,
            request=apply_request,
            print_forms=bank_print_forms,
            credit_goods=application.credit_goods,
            reference_id=reference_id,
            hook_url=hook_url,
            success_url=success_url,
            failure_url=failure_url,
        )
        await self._log_event(
            "FF_APPLY_REQUEST",
            factoring_id=application.id,
            source="FF_FACTORING",
            payload=bank_payload,
        )
        try:
            response_payload = await self._apply_with_reauth(provider=provider, payload=bank_payload)
        except HTTPException as exc:
            await self._log_event(
                "FF_APPLY_FAILED",
                factoring_id=application.id,
                source="FF_FACTORING",
                payload={"error": self._extract_error_message(exc), "request": bank_payload},
            )
            raise

        application_uuid = response_payload.get("uuid")
        if not isinstance(application_uuid, str) or not application_uuid:
            await self._log_event(
                "FF_APPLY_FAILED",
                factoring_id=application.id,
                source="FF_FACTORING",
                payload={"error": "Bank did not return uuid", "response": response_payload},
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Freedom Factoring did not return application uuid.",
            )
        redirect_url = self._extract_redirect_url(response_payload)
        await self.repository.update_application_after_apply(
            application_id=application.id,
            uuid=application_uuid,
            redirect_url=redirect_url,
            status="IN_PROGRESS",
            reference_id=reference_id,
        )
        await self._log_event(
            "CREATED",
            factoring_id=application.id,
            source="FF_FACTORING",
            payload={
                "response": response_payload,
                "request": bank_payload,
                "status": "IN_PROGRESS",
            },
        )
        return CreateFactoringApplicationResponse(
            id=application.id,
            uuid=application_uuid,
            reference_id=reference_id,
            credit_contract=application.credit_contract,
            status="IN_PROGRESS",
            redirect_url=redirect_url,
            provider_code=PROVIDER_CODE,
        )

    async def get_print_form_file(
        self,
        application_id: int,
        name: str,
        token: str,
    ) -> bytes:
        application = await self.get_application_by_id(application_id)
        form = self._find_print_form(application, name)
        stored_token = str(form.get("file_token") or "")
        incoming = token or ""
        if (
            not stored_token
            or len(stored_token) != len(incoming)
            or not compare_digest(stored_token, incoming)
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print form not found.")
        cached = self._print_form_cache_path(application_id, name)
        if cached.exists():
            return cached.read_bytes()
        signed = await self._is_print_form_signed(form)
        if not signed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Документ ещё не подписан.",
            )
        sign_process_id = str(form.get("sign_process_id") or "")
        try:
            pdf = await self._require_mynca().sign_download_pdf(sign_process_id)
        except MyncaClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=exc.detail,
            ) from exc
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(pdf)
        return pdf

    async def get_application_by_id(self, application_id: int) -> FactoringApplicationResponse:
        application = await self.repository.get_application_by_id(application_id)
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"factoring application id={application_id} was not found.",
            )
        return application

    async def get_applications_by_client_request(
        self, client_request_id: int
    ) -> list[FactoringApplicationResponse]:
        return await self.repository.get_applications_by_client_request(client_request_id)

    async def handle_webhook(
        self,
        payload: dict[str, Any],
        *,
        authorization_header: str | None,
    ) -> WebhookAckResponse:
        await self._verify_webhook_auth_if_configured(authorization_header)

        status_value = self._extract_status(payload)
        reference_id = self._extract_string(payload, "reference_id")
        uuid = self._extract_string(payload, "uuid")
        application = await self.repository.get_application_by_reference_or_uuid(
            reference_id=reference_id,
            uuid=uuid,
        )
        if application is None:
            await self._log_event(
                "WEBHOOK_ORPHAN",
                source="FF_FACTORING",
                payload=payload,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factoring application was not found for webhook payload.",
            )

        approved_params = self._build_approved_params(payload)
        await self.repository.update_application_from_webhook(
            application_id=application.id,
            status=status_value,
            approved_params=approved_params,
            uuid=uuid,
        )
        await self._log_event(
            "WEBHOOK",
            factoring_id=application.id,
            source="FF_FACTORING",
            payload={"status": status_value, "raw": payload},
        )
        return WebhookAckResponse(ok=True)

    async def _require_provider(self) -> FactoringProvider:
        provider = await self.repository.get_provider_by_code(PROVIDER_CODE)
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Provider {PROVIDER_CODE} is not configured.",
            )
        return provider

    async def _ensure_valid_token(self, provider: FactoringProvider) -> str:
        token = await self.repository.get_token(provider.id)
        if token is not None and token.expires_at > datetime.now(UTC) + timedelta(minutes=1):
            return token.access_token
        return await self._authenticate_and_store_token(provider)

    async def _authenticate_and_store_token(self, provider: FactoringProvider) -> str:
        credentials = await self.repository.get_active_credentials(provider.id, self.app_env)
        if credentials is None:
            # fallback: try stage if APP_ENV differs
            credentials = await self.repository.get_active_credentials(provider.id, "stage")
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Active factoring credentials were not found for env={self.app_env}.",
            )

        auth_path = provider.config.get("auth_path")
        if not isinstance(auth_path, str) or not auth_path.strip():
            auth_path = "/ffc-api-auth/"

        try:
            access_token, refresh_token = await self.client.authenticate(
                username=credentials.username,
                password=credentials.password,
                auth_path=auth_path,
                **self._request_kwargs(provider),
            )
        except FactoringClientError as exc:
            raise self._map_client_error(exc) from exc

        expires_at = datetime.now(UTC) + timedelta(minutes=55)
        await self.repository.upsert_token(
            provider_id=provider.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        return access_token

    async def _apply_with_reauth(
        self,
        *,
        provider: FactoringProvider,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        access_token = await self._ensure_valid_token(provider)
        apply_path = provider.config.get("apply_path")
        if not isinstance(apply_path, str) or not apply_path.strip():
            apply_path = "/ffc-api-public/universal/apply/apply-lead-factoring"

        try:
            return await self.client.apply_lead_factoring(
                access_token=access_token,
                payload=payload,
                apply_path=apply_path,
                **self._request_kwargs(provider),
            )
        except FactoringClientError as exc:
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                access_token = await self._authenticate_and_store_token(provider)
                try:
                    return await self.client.apply_lead_factoring(
                        access_token=access_token,
                        payload=payload,
                        apply_path=apply_path,
                        **self._request_kwargs(provider),
                    )
                except FactoringClientError as retry_exc:
                    raise self._map_client_error(retry_exc) from retry_exc
            raise self._map_client_error(exc) from exc

    def _build_apply_payload(
        self,
        *,
        provider: FactoringProvider,
        iin: str,
        phone: str,
        product_id: str,
        partner: str,
        channel: str,
        credit_contract: str,
        request: CreateFactoringApplicationRequest,
        print_forms: list[dict[str, Any]],
        credit_goods: list[dict[str, Any]] | None,
        reference_id: str,
        hook_url: str,
        success_url: str,
        failure_url: str,
    ) -> dict[str, Any]:
        credit_params: dict[str, Any] = {
            "period": request.period,
            "principal": float(request.principal),
        }
        if request.prepayment_amount is not None:
            credit_params["prepayment_amount"] = float(request.prepayment_amount)
        if request.interest_rate is not None:
            credit_params["interest_rate"] = float(request.interest_rate)

        payload: dict[str, Any] = {
            "iin": iin,
            "mobile_phone": phone,
            "product": product_id,
            "partner": partner,
            "channel": channel,
            "credit_contract": credit_contract,
            "credit_params": credit_params,
            "print_forms": print_forms,
            "credit_configs": {"is_knox": request.is_knox},
            "additional_information": {
                "hook_url": hook_url,
                "failure_url": failure_url,
                "success_url": success_url,
                "reference_id": reference_id,
            },
            "reference_id": reference_id,
        }
        if credit_goods:
            payload["credit_goods"] = credit_goods
        return payload

    @staticmethod
    def _generate_credit_contract(
        *,
        branch_code: str,
        client_request_id: int,
        sequence: int = 1,
    ) -> str:
        yy = datetime.now(UTC).strftime("%y")
        seq = str(client_request_id) if sequence <= 1 else f"{client_request_id}-{sequence}"
        return f"FCT{yy}-{branch_code}-{seq}"

    def _require_mynca(self) -> MyncaClient:
        if self.mynca is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MyNCA client is not configured.",
            )
        return self.mynca

    @staticmethod
    def _template_values(
        *,
        client_fio: str,
        iin: str,
        phone: str,
        principal: Any,
        period: int,
        credit_contract: str,
    ) -> dict[str, str]:
        amount = f"{principal:,.0f}".replace(",", " ")
        created_at = datetime.now(UTC).strftime("%d.%m.%Y")
        return {
            "borrower_full_name": client_fio,
            "borrower_iin": iin,
            "borrower_number": phone,
            "borrower_otp": "",
            "principal": amount,
            "principal_kz": amount,
            "principal_ru": amount,
            "period": str(period),
            "created_at": created_at,
            "contract_number": credit_contract,
            "quantity": "1",
            "total_amount": amount,
        }

    async def _prepare_one_print_form(
        self,
        *,
        spec: dict[str, str],
        placeholders: dict[str, str],
        client_request_id: int,
    ) -> dict[str, Any]:
        template = await self.repository.get_template_by_code(spec["template_code"])
        path = str((template or {}).get("template_path") or "").strip()
        docx_bytes = await fetch_template_bytes(
            path,
            self.office_public_url,
            spec["template_code"],
        )
        filled = fill_docx_bytes(docx_bytes, placeholders)
        mynca = self._require_mynca()
        try:
            pdf_bytes = await mynca.docx_to_pdf(filled)
            sign_url, sign_process_id = await mynca.sign_create(
                file_name=spec["file_name"],
                pdf_bytes=pdf_bytes,
                ext_id=client_request_id,
                meta_data={
                    "type_code": "FACTORING_PRINT_FORM",
                    "doc_type": spec["name"].upper(),
                    "client_request_id": client_request_id,
                    "print_form": spec["name"],
                },
                back_url=f"{self.public_base_url}/api/v1/factoring/ff/sign-callback",
                return_url=f"{self.public_base_url}/api/v1/factoring/ff/sign-callback",
            )
        except MyncaClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=exc.detail,
            ) from exc
        return {
            "name": spec["name"],
            "title": spec["title"],
            "url": "",
            "file_token": token_hex(16),
            "sign_url": sign_url,
            "sign_process_id": sign_process_id,
            "signed": False,
        }

    def _print_form_public_url(self, application_id: int, form: dict[str, Any]) -> str:
        name = str(form.get("name") or "")
        token = str(form.get("file_token") or "")
        return (
            f"{self.public_base_url}/api/v1/factoring/ff/print-forms/"
            f"{application_id}/{name}?t={token}"
        )

    def _to_sign_document(
        self,
        form: dict[str, Any],
        *,
        application_id: int,
        signed: bool | None = None,
    ) -> FactoringSignDocument:
        is_signed = bool(form.get("signed")) if signed is None else signed
        url = self._print_form_public_url(application_id, form) if is_signed else None
        return FactoringSignDocument(
            name=str(form.get("name") or ""),
            title=str(form.get("title") or form.get("name") or ""),
            sign_url=str(form.get("sign_url") or "") or None,
            signed=is_signed,
            url=url,
        )

    @staticmethod
    def _print_forms_list(application: FactoringApplicationResponse) -> list[dict[str, Any]]:
        raw = application.print_forms or []
        return [dict(item) for item in raw if isinstance(item, dict)]

    def _find_print_form(
        self,
        application: FactoringApplicationResponse,
        name: str,
    ) -> dict[str, Any]:
        for item in self._print_forms_list(application):
            if item.get("name") == name:
                return item
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print form not found.")

    async def _is_print_form_signed(self, form: dict[str, Any]) -> bool:
        if form.get("signed"):
            return True
        sign_process_id = str(form.get("sign_process_id") or "")
        if not sign_process_id:
            return False
        try:
            status_value = await self._require_mynca().sign_status(sign_process_id)
        except MyncaClientError as exc:
            logger.warning(
                "MyNCA sign status failed | sign_process_id={id} error={error}",
                id=sign_process_id,
                error=exc.detail,
            )
            return False
        return status_value in SIGNED_MYNCA_STATUSES

    async def _poll_print_form_signatures(
        self,
        application: FactoringApplicationResponse,
    ) -> list[FactoringSignDocument]:
        documents: list[FactoringSignDocument] = []
        for form in self._print_forms_list(application):
            signed = await self._is_print_form_signed(form)
            documents.append(
                self._to_sign_document(form, application_id=application.id, signed=signed)
            )
        return documents

    @staticmethod
    def _print_form_cache_path(application_id: int, name: str) -> Path:
        safe_name = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_"}) or "doc"
        return PRINT_FORMS_CACHE_DIR / str(application_id) / f"{safe_name}.pdf"

    @staticmethod
    def _extract_redirect_url(payload: dict[str, Any]) -> str | None:
        for key in ("redirect_url", "url"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _required_config_value(provider: FactoringProvider, key: str) -> str:
        value = provider.config.get(key)
        if isinstance(value, str) and value.strip():
            return value
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FF_FACTORING provider config.{key} is missing.",
        )

    @staticmethod
    def _provider_resolve_ip(provider: FactoringProvider) -> str | None:
        value = provider.config.get("resolve_ip")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @classmethod
    def _request_kwargs(cls, provider: FactoringProvider) -> dict[str, str | None]:
        return {
            "base_url": provider.base_url,
            "resolve_ip": cls._provider_resolve_ip(provider),
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
    def _map_client_error(exc: FactoringClientError) -> HTTPException:
        detail = exc.detail.strip() or "Freedom Factoring request failed."
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            return HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=detail,
            )
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Freedom Factoring authentication failed.",
            )
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )

    @staticmethod
    def _extract_error_message(exc: HTTPException) -> str:
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        return str(detail)

    async def _log_event(
        self,
        event_type: str,
        *,
        factoring_id: int | None = None,
        source: str,
        payload: dict[str, Any],
    ) -> None:
        try:
            await self.repository.insert_event_log(
                factoring_id=factoring_id,
                event_type=event_type,
                payload=payload,
                source=source,
            )
        except Exception as exc:  # noqa: BLE001 — audit must not break main flow
            logger.warning(
                "Factoring event log write failed | event_type={event_type} "
                "factoring_id={factoring_id} error={error}",
                event_type=event_type,
                factoring_id=factoring_id,
                error=exc,
            )

    async def _verify_webhook_auth_if_configured(self, authorization_header: str | None) -> None:
        credentials = await self.repository.get_provider_webhook_credentials(code=PROVIDER_CODE)
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
    def _invalid_webhook_credentials_exception() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

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
    def _verify_webhook_password(password: str, credentials: FactoringWebhookCredential) -> bool:
        try:
            return checkpw(password.encode(), credentials.password_hash.encode())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid webhook password hash configuration.",
            ) from exc

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
        if status_value not in VALID_WEBHOOK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported status: {status_value}",
            )
        return status_value

    def _build_approved_params(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        source = payload.get("approved_params")
        approved_params = dict(source) if isinstance(source, dict) else {}
        for key in ("alternative_reason", "status_reason"):
            value = self._extract_string(payload, key)
            if value is not None:
                approved_params[key] = value
        return approved_params or None
