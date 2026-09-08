from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from src.config import payments_config
from src.service import BaseService

from ..forte_client import ForteClient
from ..forte_xml import forte_create_order_xml, forte_order_status_xml
from ..settings_repo import PaymentSettingsRepository
from ..shared_repo import PaymentsRepository

_FORTE_FAIL_STATUSES = frozenset({"CANCELED", "DECLINED", "EXPIRED", "ERROR"})


async def _resolve_forte_setting(settings: PaymentSettingsRepository, env_val: str, code: str) -> str:
    if env_val:
        return env_val
    db_val = await settings.get_setting_value_by_code(code)
    return db_val or ""


class FortePayService(BaseService):
    def __init__(
        self,
        repository: PaymentsRepository,
        settings: PaymentSettingsRepository,
        forte: ForteClient,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.forte = forte

    async def handle(
        self,
        mode: str,
        request_hash: str | None,
        payment_hash: str | None,
        base_url: str,
        params: dict[str, object],
    ) -> Response:
        if mode == "status":
            return PlainTextResponse(content=await self._poll_status())

        if mode == "register":
            return await self._register(request_hash, payment_hash, base_url)

        if mode in ("on_approve", "on_cancel", "on_decline"):
            return await self._redirect_back(request_hash, payment_hash)

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

        row = await self.repository.payment_client_request_get(payment_hash, request_hash)
        if row is None:
            return PlainTextResponse("Платеж не найден")

        merchant = await _resolve_forte_setting(self.settings, payments_config.forte_merchant, "FORTE_MERCHANT")
        forte_url = await _resolve_forte_setting(self.settings, payments_config.forte_url, "FORTE_URL")
        prefix = f"{base_url}/api/payments/forte-pay/mode"
        xml = forte_create_order_xml(
            merchant=merchant,
            amount_tenge_kopecks=int(float(row["payment_amount"]) * 100),
            description=str(row.get("payment_info") or ""),
            approve_url=f"{prefix}/on_approve/request/{request_hash}/payment/{payment_hash}",
            cancel_url=f"{prefix}/on_cancel/request/{request_hash}/payment/{payment_hash}",
            decline_url=f"{prefix}/on_decline/request/{request_hash}/payment/{payment_hash}",
            phone=row.get("phone_number"),
        )
        result = await self.forte.post_xml(forte_url, xml)
        if not result or result[0].get("Status") != "00":
            return PlainTextResponse("Forte CreateOrder failed", status_code=502)

        order = result[0].get("Order") or {}
        await self.repository.forte_transaction_set(
            row["client_request_payment_id"],
            row["client_request_id"],
            order.get("SessionID"),
            order.get("OrderID"),
        )
        redirect_url = f"{order.get('URL')}?sessionId={order.get('SessionID')}&orderId={order.get('OrderID')}"
        return RedirectResponse(url=redirect_url, status_code=302)

    async def _redirect_back(self, request_hash: str | None, payment_hash: str | None) -> Response:
        url = (
            f"{payments_config.public_base_url}/client/payment-request/"
            f"request/{request_hash}/payment/{payment_hash}"
        )
        return RedirectResponse(url=url, status_code=302)

    async def _poll_status(self) -> str:
        merchant = await _resolve_forte_setting(self.settings, payments_config.forte_merchant, "FORTE_MERCHANT")
        forte_url = await _resolve_forte_setting(self.settings, payments_config.forte_url, "FORTE_URL")
        pending = await self.repository.forte_payment_read_for_status()

        for item in pending:
            xml = forte_order_status_xml(
                merchant=merchant,
                order_id=item.get("order_id"),
                session_id=item.get("cp_transaction_id"),
            )
            result = await self.forte.post_xml(forte_url, xml)
            if not result:
                continue
            first = result[0]
            order = first.get("Order") or {}
            if order.get("OrderStatus") in _FORTE_FAIL_STATUSES:
                await self.repository.forte_transaction_set(
                    item["client_request_payment_id"],
                    item["client_request_id"],
                    None,
                    None,
                )
            if first.get("Status") == "00" and order.get("OrderStatus") == "APPROVED":
                await self.repository.forte_client_request_payment_set(
                    item["client_request_payment_id"],
                    item["client_request_id"],
                    order.get("OrderID"),
                    "",
                )
        return "0"
