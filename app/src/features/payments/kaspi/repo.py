import json
from typing import Any

from src.repository import BaseRepository
from src.repository.base import SpRow, SpRows

from ..constants import CLIENT_MODULE_CODE, PUBLIC_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_payments_database_error


class KaspiRepository(BaseRepository):
    async def kaspi_check(
        self,
        client_request_id: object | None,
        client_request_payment_id: object | None,
        iin: str,
        command: str,
        pay_type: int,
        sum_value: object,
        txn_id: str,
    ) -> int:
        try:
            rows = await self.call_sp(
                "client.kaspi_check",
                client_request_id,
                client_request_payment_id,
                iin,
                command,
                pay_type,
                sum_value,
                txn_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        return int(value) if value is not None else 0

    async def kaspi_request_get_info(
        self,
        client_request_id: object,
        iin: str,
    ) -> SpRow | None:
        return await self._cursor_row(
            "client.kaspi_request_get_info",
            client_request_id,
            iin,
        )

    async def kaspi_payment_get_info(
        self,
        client_request_payment_id: object,
        iin: str,
    ) -> SpRow | None:
        return await self._cursor_row(
            "client.kaspi_payment_get_info",
            client_request_payment_id,
            iin,
        )

    async def kaspi_request_pay(
        self,
        account: object,
        iin: str,
        sum_value: object,
        txn_id: str,
        txn_date: str | None,
    ) -> int:
        try:
            rows = await self.call_sp(
                "client.kaspi_request_pay",
                account,
                iin,
                sum_value,
                txn_id,
                txn_date,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        payment_id = int(value) if value is not None else 0
        if payment_id:
            await self.after_payment_operations(payment_id)
        return payment_id

    async def kaspi_payment_pay(
        self,
        account: object,
        iin: str,
        sum_value: object,
        txn_id: str,
    ) -> int:
        try:
            rows = await self.call_sp(
                "client.kaspi_payment_pay",
                account,
                iin,
                sum_value,
                txn_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        value = scalar_from_sp_rows(rows)
        payment_id = int(value) if value is not None else 0
        if payment_id:
            await self.after_payment_operations(payment_id)
        return payment_id

    async def after_payment_operations(self, client_request_payment_id: int) -> None:
        try:
            await self.call_sp(
                "public.after_payment_operations",
                client_request_payment_id,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def insert_kaspi_pay_log(
        self,
        *,
        kaspi_what: str,
        response_in: str,
        response_out: str,
        account: object,
        txn_id: str,
        sum_value: object,
        txn_date: str | None,
        pay_type: int,
        kaspi_pay_status: int,
    ) -> None:
        try:
            await self.call_sp(
                "client.insert_kaspi_pay_log",
                kaspi_what,
                response_in,
                response_out,
                account,
                txn_id,
                sum_value,
                txn_date,
                pay_type,
                kaspi_pay_status,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def _cursor_row(self, sp_name: str, *args: Any) -> SpRow | None:
        try:
            rows: SpRows = await self.call_sp(
                sp_name,
                *args,
                cursor=True,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        return rows[0] if rows else None

    @staticmethod
    def params_json(params: dict[str, Any]) -> str:
        return json.dumps(params, ensure_ascii=False)
