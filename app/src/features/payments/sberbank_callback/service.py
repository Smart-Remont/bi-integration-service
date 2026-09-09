import json
from typing import Any

from src.service import BaseService

from ..sberbank_client import SberbankClient
from ..shared_repo import PaymentsRepository


def _payment_id(value: object) -> int | None:
    """Query params are strings; SP expects integer payment id."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return None


class SberbankCallbackService(BaseService):
    def __init__(self, repository: PaymentsRepository, sber: SberbankClient) -> None:
        self.repository = repository
        self.sber = sber

    async def handle(self, params: dict[str, Any]) -> str:
        order_number = _payment_id(params.get("orderNumber"))
        if order_number is None:
            return "0"

        row = await self.repository.payment_client_request_get_by_id(order_number)
        if row is None:
            return "0"

        payment_amount = row.get("payment_amount", 0)
        await self.repository.insert_sberbank_pay_log(
            "CALLBACK",
            "",
            json.dumps(params, ensure_ascii=False),
            row["client_request_id"],
            order_number,
            float(payment_amount) * 100 if payment_amount is not None else 0,
            params.get("mdOrder"),
        )

        operation = params.get("operation")
        status = params.get("status")
        if operation == "deposited":
            if str(status) == "1":
                status_ext = await self.sber.get_order_status_extended(
                    params.get("mdOrder"),
                    order_number,
                )
                await self.repository.sberbank_client_request_payment_set(
                    order_number,
                    row["client_request_id"],
                    params.get("mdOrder"),
                    PaymentsRepository.bank_info_json(status_ext.get("bankInfo")),
                )
            else:
                await self.repository.sberbank_transaction_set(
                    order_number,
                    row["client_request_id"],
                    None,
                )
        return "0"
