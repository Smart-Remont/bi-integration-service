import json
from typing import Any

from src.repository import BaseRepository
from src.repository.base import SpRow

from ..constants import CLIENT_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_payments_database_error


class CloudPaymentsRepository(BaseRepository):
    async def cloud_payments_pay(
        self,
        mode: str,
        client_request_id_hash: str,
        client_request_payment_id_hash: str,
        amount: int,
        cp_response: str,
        cp_transaction_id: str,
    ) -> int:
        try:
            rows = await self.call_sp(
                "client.cloud_payments_pay",
                mode,
                client_request_id_hash,
                client_request_payment_id_hash,
                amount,
                cp_response,
                cp_transaction_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        return int(value) if value is not None else 0

    async def payment_client_request_get(
        self,
        payment_hash: str,
        request_hash: str,
    ) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "client.payment_client_request_get",
                payment_hash,
                request_hash,
                cursor=True,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        if not rows:
            return None
        value = scalar_from_sp_rows(rows)
        if isinstance(value, dict):
            return value
        return rows[0]

    @staticmethod
    def cp_response_json(payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False)
