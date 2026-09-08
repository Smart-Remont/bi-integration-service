import json

from src.repository import BaseRepository
from src.repository.base import SpRow, SpRows

from .constants import CLIENT_MODULE_CODE, PUBLIC_MODULE_CODE
from .db import scalar_from_sp_rows
from .errors import to_payments_database_error


class PaymentsRepository(BaseRepository):
    async def sberbank_payment_read_for_status(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.sberbank_payment_read_for_status",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def forte_payment_read_for_status(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.forte_payment_read_for_status",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def paybox_payment_read_for_status(self) -> SpRows:
        try:
            return await self.call_sp(
                "public.paybox_payment_read_for_status",
                cursor=True,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def sberbank_check(
        self,
        payment_hash: str,
        request_hash: str,
    ) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "client.sberbank_check",
                payment_hash,
                request_hash,
                cursor=True,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        return rows[0] if rows else None

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
        value = scalar_from_sp_rows(rows) if rows else None
        if isinstance(value, dict):
            return value
        return rows[0] if rows else None

    async def payment_client_request_get_by_id(
        self,
        client_request_payment_id: object,
    ) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "client.payment_client_request_get_by_id",
                client_request_payment_id,
                cursor=True,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc
        value = scalar_from_sp_rows(rows) if rows else None
        if isinstance(value, dict):
            return value
        return rows[0] if rows else None

    async def insert_sberbank_pay_log(
        self,
        what: str,
        out: str,
        inp: str,
        client_request_id: object,
        client_request_payment_id: object,
        amount: object,
        order_id: object | None,
    ) -> None:
        try:
            await self.call_sp(
                "client.insert_sbebank_pay_log",
                what,
                out,
                inp,
                client_request_id,
                client_request_payment_id,
                amount,
                order_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def sberbank_client_request_payment_set(
        self,
        client_request_payment_id: object,
        client_request_id: object,
        transaction_id: object,
        bank_info: str,
    ) -> None:
        try:
            await self.call_sp(
                "client.sberbank_client_request_payment_set",
                client_request_payment_id,
                client_request_id,
                transaction_id,
                bank_info,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def sberbank_transaction_set(
        self,
        client_request_payment_id: object,
        client_request_id: object,
        transaction_id: object | None,
    ) -> None:
        try:
            await self.call_sp(
                "client.sberbank_transaction_set",
                client_request_payment_id,
                client_request_id,
                transaction_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def paybox_transaction_set(
        self,
        client_request_payment_id: object,
        client_request_id: object,
        transaction_id: object | None,
    ) -> None:
        try:
            await self.call_sp(
                "client.paybox_transaction_set",
                client_request_payment_id,
                client_request_id,
                transaction_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def paybox_client_request_payment_set(
        self,
        client_request_payment_id: object,
        client_request_id: object,
        transaction_id: object,
        bank_info: str,
    ) -> None:
        try:
            await self.call_sp(
                "client.paybox_client_request_payment_set",
                client_request_payment_id,
                client_request_id,
                transaction_id,
                bank_info,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def forte_transaction_set(
        self,
        client_request_payment_id: object,
        client_request_id: object,
        session_id: object | None,
        order_id: object | None,
    ) -> None:
        try:
            await self.call_sp(
                "client.forte_transaction_set",
                client_request_payment_id,
                client_request_id,
                session_id,
                order_id,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    async def forte_client_request_payment_set(
        self,
        client_request_payment_id: object,
        client_request_id: object,
        order_id: object,
        bank_info: str,
    ) -> None:
        try:
            await self.call_sp(
                "client.forte_client_request_payment_set",
                client_request_payment_id,
                client_request_id,
                order_id,
                bank_info,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_payments_database_error(exc) from exc

    @staticmethod
    def bank_info_json(bank_info: object | None) -> str:
        if bank_info is None:
            return ""
        return json.dumps(bank_info, ensure_ascii=False)
