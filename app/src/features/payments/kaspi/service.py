from __future__ import annotations

import json
from typing import Any

from loguru import logger
from src.config import payments_config
from src.service import BaseService

from ..errors import PaymentsDatabaseError
from .repo import KaspiRepository
from .xml import check_success_xml, error_xml, info_fields, pay_success_xml


def _kaspi_int(value: object, default: int = 0) -> int:
    """Query params from HTTP are strings; SP expects integer ids/amounts."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return default
    if text.isdigit():
        return int(text)
    try:
        return int(float(text))
    except ValueError:
        return default


class KaspiService(BaseService):
    def __init__(self, repository: KaspiRepository) -> None:
        self.repository = repository

    async def handle_request_pay(
        self,
        *,
        client_ip: str,
        params: dict[str, Any],
    ) -> tuple[str, int]:
        if not self._ip_allowed(client_ip):
            return error_xml(None, 403, "Forbidden"), 403

        command = str(params.get("command") or "")
        if command == "check":
            return await self._request_check(params)
        if command == "pay":
            return await self._request_pay(params)
        return error_xml(params.get("txn_id"), 5, "Unknown command"), 200

    async def handle_payment_pay(
        self,
        *,
        client_ip: str,
        params: dict[str, Any],
    ) -> tuple[str, int]:
        if not self._ip_allowed(client_ip):
            return error_xml(None, 403, "Forbidden"), 403

        command = str(params.get("command") or "")
        if command == "check":
            return await self._payment_check(params)
        if command == "pay":
            return await self._payment_pay(params)
        return error_xml(params.get("txn_id"), 5, "Unknown command"), 200

    async def _request_check(self, params: dict[str, Any]) -> tuple[str, int]:
        txn_id = str(params.get("txn_id") or "")
        iin = str(params.get("iin") or "")
        account = _kaspi_int(params.get("account", 0))
        sum_value = _kaspi_int(params.get("sum", 0))
        params_json = KaspiRepository.params_json(params)

        try:
            check_code = await self.repository.kaspi_check(
                account,
                None,
                iin,
                "check",
                1,
                sum_value,
                txn_id,
            )
        except PaymentsDatabaseError as exc:
            xml = error_xml(txn_id, 5, exc.message)
            await self._log("check", params_json, xml, account, txn_id, sum_value, None, 1, 2)
            return xml, 200

        if check_code != 0:
            xml = error_xml(txn_id, check_code)
            await self._log("check", params_json, xml, account, txn_id, sum_value, None, 1, 2)
            return xml, 200

        info = await self.repository.kaspi_request_get_info(account, iin)
        if info is None:
            xml = error_xml(txn_id, 5, "No request info")
            await self._log("check", params_json, xml, account, txn_id, sum_value, None, 1, 2)
            return xml, 200

        xml = check_success_xml(
            txn_id=txn_id,
            result_code=check_code,
            company_bin=str(info.get("company_bin") or ""),
            fields=info_fields(info),
        )
        await self._log("check", params_json, xml, account, txn_id, sum_value, None, 1, 1)
        return xml, 200

    async def _request_pay(self, params: dict[str, Any]) -> tuple[str, int]:
        txn_id = str(params.get("txn_id") or "")
        txn_date = str(params.get("txn_date") or "") or None
        iin = str(params.get("iin") or "")
        account = _kaspi_int(params.get("account", 0))
        sum_value = _kaspi_int(params.get("sum", 0))
        params_json = KaspiRepository.params_json(params)

        try:
            check_code = await self.repository.kaspi_check(
                account,
                None,
                iin,
                "pay",
                1,
                sum_value,
                txn_id,
            )
        except PaymentsDatabaseError as exc:
            xml = error_xml(txn_id, 5, exc.message)
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 1, 2)
            return xml, 200

        if check_code != 0:
            xml = error_xml(txn_id, check_code)
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 1, 2)
            return xml, 200

        try:
            prv_txn = await self.repository.kaspi_request_pay(
                account,
                iin,
                sum_value,
                txn_id,
                txn_date,
            )
        except PaymentsDatabaseError as exc:
            xml = error_xml(txn_id, 5, exc.message)
            await self._log("pay", json.dumps({"error": exc.message}), xml, account, txn_id, sum_value, txn_date, 1, 2)
            return xml, 200

        if not prv_txn:
            xml = error_xml(txn_id, 5, "Payment failed")
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 1, 2)
            return xml, 200

        info = await self.repository.kaspi_request_get_info(account, iin)
        company_bin = str((info or {}).get("company_bin") or "")
        xml = pay_success_xml(
            txn_id=txn_id,
            prv_txn=prv_txn,
            sum_value=sum_value,
            result_code=check_code,
            company_bin=company_bin,
        )
        await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 1, 1)
        return xml, 200

    async def _payment_check(self, params: dict[str, Any]) -> tuple[str, int]:
        txn_id = str(params.get("txn_id") or "")
        iin = str(params.get("iin") or "")
        account = _kaspi_int(params.get("account", 0))
        sum_value = _kaspi_int(params.get("sum", 0))
        params_json = KaspiRepository.params_json(params)

        try:
            check_code = await self.repository.kaspi_check(
                None,
                account,
                iin,
                "check",
                2,
                sum_value,
                txn_id,
            )
        except PaymentsDatabaseError as exc:
            xml = error_xml(txn_id, 5, exc.message)
            await self._log("check", params_json, xml, account, txn_id, sum_value, None, 2, 2)
            return xml, 200

        if check_code != 0:
            xml = error_xml(txn_id, check_code)
            await self._log("check", params_json, xml, account, txn_id, sum_value, None, 2, 2)
            return xml, 200

        info = await self.repository.kaspi_payment_get_info(account, iin)
        if info is None:
            xml = error_xml(txn_id, 5, "No payment info")
            await self._log("check", params_json, xml, account, txn_id, sum_value, None, 2, 2)
            return xml, 200

        xml = check_success_xml(
            txn_id=txn_id,
            result_code=check_code,
            company_bin=str(info.get("company_bin") or ""),
            fields=info_fields(info),
            payment_amount=info.get("payment_amount"),
        )
        await self._log("check", params_json, xml, account, txn_id, sum_value, None, 2, 1)
        return xml, 200

    async def _payment_pay(self, params: dict[str, Any]) -> tuple[str, int]:
        txn_id = str(params.get("txn_id") or "")
        txn_date = str(params.get("txn_date") or "") or None
        iin = str(params.get("iin") or "")
        account = _kaspi_int(params.get("account", 0))
        sum_value = _kaspi_int(params.get("sum", 0))
        params_json = KaspiRepository.params_json(params)

        try:
            check_code = await self.repository.kaspi_check(
                None,
                account,
                iin,
                "pay",
                2,
                sum_value,
                txn_id,
            )
        except PaymentsDatabaseError as exc:
            xml = error_xml(txn_id, 5, exc.message)
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 2, 2)
            return xml, 200

        if check_code != 0:
            xml = error_xml(txn_id, check_code)
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 2, 2)
            return xml, 200

        try:
            prv_txn = await self.repository.kaspi_payment_pay(account, iin, sum_value, txn_id)
        except PaymentsDatabaseError as exc:
            xml = error_xml(txn_id, 5, exc.message)
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 2, 2)
            return xml, 200

        if not prv_txn:
            xml = error_xml(txn_id, 5, "Payment failed")
            await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 2, 2)
            return xml, 200

        info = await self.repository.kaspi_payment_get_info(account, iin)
        company_bin = str((info or {}).get("company_bin") or "")
        xml = pay_success_xml(
            txn_id=txn_id,
            prv_txn=prv_txn,
            sum_value=sum_value,
            result_code=check_code,
            company_bin=company_bin,
        )
        await self._log("pay", params_json, xml, account, txn_id, sum_value, txn_date, 2, 1)
        return xml, 200

    async def _log(
        self,
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
            await self.repository.insert_kaspi_pay_log(
                kaspi_what=kaspi_what,
                response_in=response_in,
                response_out=response_out,
                account=account,
                txn_id=txn_id,
                sum_value=sum_value,
                txn_date=txn_date,
                pay_type=pay_type,
                kaspi_pay_status=kaspi_pay_status,
            )
        except PaymentsDatabaseError as exc:
            logger.warning("kaspi pay log failed: {error}", error=exc.message)

    @staticmethod
    def _ip_allowed(client_ip: str) -> bool:
        allowed = payments_config.kaspi_allowed_ips
        if not allowed:
            return True
        return client_ip in allowed
