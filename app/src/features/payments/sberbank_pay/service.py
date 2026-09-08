import json
from typing import Any

from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from src.config import payments_config
from src.service import BaseService

from ..sberbank_client import SberbankClient
from ..shared_repo import PaymentsRepository


class SberbankPayService(BaseService):
    """Legacy ``sberbankPayAction`` modes: register, status, postlink."""

    def __init__(self, repository: PaymentsRepository, sber: SberbankClient) -> None:
        self.repository = repository
        self.sber = sber

    async def handle(
        self,
        mode: str,
        request_hash: str | None,
        payment_hash: str | None,
        base_url: str,
        extra: dict[str, Any],
    ) -> Response:
        if mode == "register":
            return await self._register(request_hash, payment_hash, base_url)
        if mode == "status":
            return await self._status(extra)
        if mode == "postlink":
            return await self._postlink(request_hash, payment_hash, base_url, extra)
        return PlainTextResponse("Неподдерживаемый mode", status_code=400)

    async def _register(
        self,
        request_hash: str | None,
        payment_hash: str | None,
        base_url: str,
    ) -> Response:
        if not request_hash or not payment_hash:
            return PlainTextResponse("request/payment обязательны", status_code=400)

        check = await self.repository.sberbank_check(payment_hash, request_hash)
        if check is None:
            return PlainTextResponse("Платеж не найден")

        return_url = (
            f"{base_url}/api/payments/sberbank-pay/mode/postlink/"
            f"request/{request_hash}/payment/{payment_hash}"
        )
        amount = int(float(check["payment_amount"]) * 100)
        out = {
            "order_id": check["client_request_payment_id"],
            "amount": amount,
            "return_url": return_url,
        }
        result = await self.sber.register(out["order_id"], amount, return_url)
        if result.get("errorCode") not in (0, "0", None) and result.get("errorCode") != 0:
            await self.repository.insert_sberbank_pay_log(
                "register",
                json.dumps(out, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                check["client_request_id"],
                out["order_id"],
                amount,
                None,
            )
            return PlainTextResponse(str(result.get("errorMessage", "Sber error")))

        await self.repository.insert_sberbank_pay_log(
            "register",
            json.dumps(out, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            check["client_request_id"],
            out["order_id"],
            amount,
            result.get("orderId"),
        )
        form_url = result.get("formUrl")
        if not form_url:
            return PlainTextResponse("Sber не вернул formUrl", status_code=502)
        return RedirectResponse(url=str(form_url), status_code=302)

    async def _status(self, extra: dict[str, Any]) -> Response:
        result = await self.sber.get_order_status_extended(
            extra.get("order_id"),
            extra.get("order_num"),
        )
        return PlainTextResponse(content=repr(result))

    async def _postlink(
        self,
        request_hash: str | None,
        payment_hash: str | None,
        base_url: str,
        extra: dict[str, Any],
    ) -> Response:
        if not request_hash or not payment_hash:
            return PlainTextResponse("request/payment обязательны", status_code=400)

        row = await self.repository.payment_client_request_get(payment_hash, request_hash)
        if row is None:
            return PlainTextResponse("Платеж не найден")

        order_id = extra.get("orderId")
        await self.repository.sberbank_transaction_set(
            row["client_request_payment_id"],
            row["client_request_id"],
            order_id,
        )
        result = await self.sber.get_order_status_extended(order_id, None)
        client_url = (
            f"{payments_config.public_base_url}/client/payment-request/"
            f"request/{request_hash}/payment/{payment_hash}"
        )
        if result.get("actionCode") == 0:
            return RedirectResponse(url=client_url, status_code=302)
        return PlainTextResponse(str(result.get("errorMessage", "Payment failed")))
