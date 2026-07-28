import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.features.big_integration.db import scalar_from_sp_rows
from src.repository import BaseRepository

from ..schemas import FactoringApplicationResponse

PROVIDER_CODE = "FF_FACTORING"


@dataclass(slots=True, frozen=True)
class FactoringProvider:
    id: int
    code: str
    base_url: str
    config: dict[str, Any]


@dataclass(slots=True, frozen=True)
class FactoringCredential:
    username: str
    password: str


@dataclass(slots=True, frozen=True)
class FactoringToken:
    access_token: str
    refresh_token: str | None
    expires_at: datetime


@dataclass(slots=True, frozen=True)
class FactoringWebhookCredential:
    username: str
    password_hash: str


@dataclass(slots=True, frozen=True)
class FactoringWebhookApplication:
    id: int
    status: str
    approved_params: dict[str, Any] | None


class FactoringRepository(BaseRepository):
    async def get_provider_by_code(self, code: str = PROVIDER_CODE) -> FactoringProvider | None:
        rows = await self.call_sp(
            "public.factoring__provider_get",
            code,
            cursor=True,
            module_code="MYSPACE",
        )
        if not rows:
            return None
        row = rows[0]

        raw_config = row["config"]
        if isinstance(raw_config, str):
            config = json.loads(raw_config)
        elif isinstance(raw_config, dict):
            config = raw_config
        else:
            config = {}

        return FactoringProvider(
            id=row["id"],
            code=row["code"],
            base_url=row["base_url"],
            config=config,
        )

    async def get_active_credentials(self, provider_id: int, env: str) -> FactoringCredential | None:
        rows = await self.call_sp(
            "public.factoring__credential_get_active",
            provider_id,
            env,
            cursor=True,
            module_code="MYSPACE",
        )
        if not rows:
            return None
        row = rows[0]
        return FactoringCredential(
            username=row["username"],
            password=row["password"],
        )

    async def get_token(self, provider_id: int) -> FactoringToken | None:
        rows = await self.call_sp(
            "public.factoring__token_get",
            provider_id,
            cursor=True,
            module_code="MYSPACE",
        )
        if not rows:
            return None
        row = rows[0]
        return FactoringToken(
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            expires_at=row["expires_at"],
        )

    async def upsert_token(
        self,
        provider_id: int,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime,
    ) -> None:
        payload = {
            "provider_id": provider_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat(),
        }
        scalar_from_sp_rows(
            await self.call_sp(
                "public.factoring__token_upsert",
                json.dumps(payload),
                module_code="MYSPACE",
            )
        )

    async def insert_application(
        self,
        *,
        client_request_id: int,
        provider_id: int,
        credit_contract: str,
        product_id: str,
        principal: Decimal,
        period: int,
        created_by: int,
        partner: str | None = None,
        channel: str | None = None,
        branch_code: str | None = None,
        reference_id: str | None = None,
        prepayment_amount: Decimal | None = None,
        interest_rate: Decimal | None = None,
        print_forms: list[dict[str, Any]] | None = None,
        credit_goods: list[dict[str, Any]] | None = None,
        request_payload: dict[str, Any] | None = None,
        success_url: str | None = None,
        failure_url: str | None = None,
        hook_url: str | None = None,
        status: str = "NEW",
    ) -> int:
        payload: dict[str, Any] = {
            "client_request_id": client_request_id,
            "provider_id": provider_id,
            "credit_contract": credit_contract,
            "product_id": product_id,
            "principal": str(principal),
            "period": period,
            "created_by": created_by,
            "status": status,
        }
        if partner is not None:
            payload["partner"] = partner
        if channel is not None:
            payload["channel"] = channel
        if branch_code is not None:
            payload["branch_code"] = branch_code
        if reference_id is not None:
            payload["reference_id"] = reference_id
        if prepayment_amount is not None:
            payload["prepayment_amount"] = str(prepayment_amount)
        if interest_rate is not None:
            payload["interest_rate"] = str(interest_rate)
        if print_forms is not None:
            payload["print_forms"] = print_forms
        if credit_goods is not None:
            payload["credit_goods"] = credit_goods
        if request_payload is not None:
            payload["request_payload"] = request_payload
        if success_url is not None:
            payload["success_url"] = success_url
        if failure_url is not None:
            payload["failure_url"] = failure_url
        if hook_url is not None:
            payload["hook_url"] = hook_url

        scalar_result = scalar_from_sp_rows(
            await self.call_sp(
                "public.factoring__application_create",
                json.dumps(payload),
                module_code="MYSPACE",
            )
        )
        if scalar_result is None:
            raise RuntimeError("Failed to insert factoring application.")
        return int(scalar_result)

    async def update_application_after_apply(
        self,
        *,
        application_id: int,
        uuid: str,
        redirect_url: str | None,
        status: str,
        reference_id: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "application_id": application_id,
            "uuid": uuid,
            "redirect_url": redirect_url,
            "status": status,
        }
        if reference_id is not None:
            payload["reference_id"] = reference_id
        scalar_from_sp_rows(
            await self.call_sp(
                "public.factoring__application_update_after_apply",
                json.dumps(payload),
                module_code="MYSPACE",
            )
        )

    async def insert_event_log(
        self,
        *,
        factoring_id: int | None,
        event_type: str,
        payload: dict[str, Any],
        source: str,
    ) -> None:
        request_payload: dict[str, Any] = {
            "event_type": event_type,
            "payload": payload,
            "source": source,
        }
        if factoring_id is not None:
            request_payload["factoring_id"] = factoring_id
        scalar_from_sp_rows(
            await self.call_sp(
                "public.factoring__event_log_add",
                json.dumps(request_payload),
                module_code="MYSPACE",
            )
        )

    def _row_to_application(self, row: dict[str, Any]) -> FactoringApplicationResponse:
        payload = dict(row)
        for key in ("approved_params", "print_forms", "credit_goods"):
            if isinstance(payload.get(key), str):
                payload[key] = json.loads(payload[key])
        return FactoringApplicationResponse.model_validate(payload)

    async def get_application_by_id(self, application_id: int) -> FactoringApplicationResponse | None:
        rows = await self.call_sp(
            "public.factoring__application_get",
            application_id,
            cursor=True,
            module_code="MYSPACE",
        )
        if not rows:
            return None
        return self._row_to_application(dict(rows[0]))

    async def get_applications_by_client_request(
        self, client_request_id: int
    ) -> list[FactoringApplicationResponse]:
        rows = await self.call_sp(
            "public.factoring__applications_list_by_client_request",
            client_request_id,
            cursor=True,
            module_code="MYSPACE",
        )
        return [self._row_to_application(dict(row)) for row in rows]

    async def client_request_exists(self, client_request_id: int) -> bool:
        rows = await self.call_sp(
            "public.factoring__client_request_get_for_apply",
            client_request_id,
            cursor=True,
            module_code="MYSPACE",
        )
        return bool(rows)

    async def get_provider_webhook_credentials(
        self, code: str = PROVIDER_CODE
    ) -> FactoringWebhookCredential | None:
        rows = await self.call_sp(
            "public.factoring__provider_webhook_credentials_get",
            code,
            cursor=True,
            module_code="MYSPACE",
        )
        if not rows:
            return None
        row = rows[0]
        username = row["webhook_username"]
        password_hash = row["webhook_password"]
        if not isinstance(username, str) or not username.strip():
            return None
        if not isinstance(password_hash, str) or not password_hash.strip():
            return None
        return FactoringWebhookCredential(username=username, password_hash=password_hash)

    async def get_application_by_reference_or_uuid(
        self,
        reference_id: str | None,
        uuid: str | None,
    ) -> FactoringWebhookApplication | None:
        if reference_id is None and uuid is None:
            return None

        rows = await self.call_sp(
            "public.factoring__application_get_by_reference_or_uuid",
            reference_id,
            uuid,
            cursor=True,
            module_code="MYSPACE",
        )
        if not rows:
            return None
        row = rows[0]
        approved_params = row["approved_params"]
        if isinstance(approved_params, str):
            approved_params = json.loads(approved_params)

        return FactoringWebhookApplication(
            id=row["id"],
            status=row["status"],
            approved_params=approved_params if isinstance(approved_params, dict) else None,
        )

    async def update_application_from_webhook(
        self,
        *,
        application_id: int,
        status: str,
        approved_params: dict[str, Any] | None = None,
        uuid: str | None = None,
        redirect_url: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "application_id": application_id,
            "status": status,
        }
        if approved_params is not None:
            payload["approved_params"] = approved_params
        if uuid is not None:
            payload["uuid"] = uuid
        if redirect_url is not None:
            payload["redirect_url"] = redirect_url
        scalar_from_sp_rows(
            await self.call_sp(
                "public.factoring__application_update_from_webhook",
                json.dumps(payload),
                module_code="MYSPACE",
            )
        )
