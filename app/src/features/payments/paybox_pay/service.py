from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from src.config import payments_config
from src.service import BaseService

from ..paybox_client import PayboxClient
from ..settings_repo import PaymentSettingsRepository
from ..shared_repo import PaymentsRepository
from ..xml_helpers import paybox_signature

_PAYBOX_FAIL_STATUSES = frozenset({"revoked", "failed", "incomplete", "refunded"})


async def _resolve_paybox(settings: PaymentSettingsRepository, env_val: str, code: str) -> str:
    if env_val:
        return env_val
    db_val = await settings.get_setting_value_by_code(code)
    return db_val or ""


class PayboxPayService(BaseService):
    def __init__(
        self,
        repository: PaymentsRepository,
        settings: PaymentSettingsRepository,
        paybox: PayboxClient,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.paybox = paybox

    async def handle(
        self,
        mode: str,
        request_hash: str | None,
        payment_hash: str | None,
        base_url: str,
    ) -> Response:
        if not payments_config.paybox_enabled:
            return PlainTextResponse("Данный метод оплаты отключен")

        if mode == "init":
            return await self._init(request_hash, payment_hash, base_url)
        if mode == "status":
            return PlainTextResponse(content=await self._poll_status())
        return PlainTextResponse("Неподдерживаемый mode", status_code=400)

    async def _init(
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

        merchant = await _resolve_paybox(self.settings, payments_config.paybox_merchant, "PAYBOX_MERCHANT")
        salt = await _resolve_paybox(self.settings, payments_config.paybox_salt, "PAYBOX_SALT")
        secret = await _resolve_paybox(self.settings, payments_config.paybox_secret_key, "PAYBOX_PAYMENT")
        init_url = await _resolve_paybox(self.settings, payments_config.paybox_init_url, "PAYBOX_INIT_PAY")

        prefix = f"{base_url}/api/payments/paybox/mode"
        data = {
            "pg_order_id": row["client_request_payment_id"],
            "pg_merchant_id": merchant,
            "pg_amount": row["payment_amount"],
            "pg_description": row.get("payment_info") or "",
            "pg_check_url": f"{prefix}/check_url/request/{request_hash}/payment/{payment_hash}",
            "pg_result_url": f"{prefix}/result_url/request/{request_hash}/payment/{payment_hash}",
            "pg_salt": salt,
        }
        data["pg_sig"] = paybox_signature(data, "init_payment.php", secret)
        result = await self.paybox.post_form(init_url, data)
        if not result or result[0].get("pg_status") != "ok":
            return PlainTextResponse("Paybox init failed", status_code=502)

        await self.repository.paybox_transaction_set(
            row["client_request_payment_id"],
            row["client_request_id"],
            result[0].get("pg_payment_id"),
        )
        return RedirectResponse(url=str(result[0]["pg_redirect_url"]), status_code=302)

    async def _poll_status(self) -> str:
        merchant = await _resolve_paybox(self.settings, payments_config.paybox_merchant, "PAYBOX_MERCHANT")
        salt = await _resolve_paybox(self.settings, payments_config.paybox_salt, "PAYBOX_SALT")
        secret = await _resolve_paybox(self.settings, payments_config.paybox_secret_key, "PAYBOX_PAYMENT")
        status_url = await _resolve_paybox(self.settings, payments_config.paybox_status_url, "PAYBOX_PAY_STATUS")

        pending = await self.repository.paybox_payment_read_for_status()
        for item in pending:
            data = {
                "pg_merchant_id": merchant,
                "pg_payment_id": item.get("cp_transaction_id"),
                "pg_order_id": item.get("client_request_payment_id"),
                "pg_salt": salt,
            }
            data["pg_sig"] = paybox_signature(data, "get_status2.php", secret)
            result = await self.paybox.post_form(status_url, data)
            if not result:
                continue
            first = result[0]
            if first.get("pg_transaction_status") in _PAYBOX_FAIL_STATUSES:
                await self.repository.paybox_transaction_set(
                    item["client_request_payment_id"],
                    item["client_request_id"],
                    None,
                )
            if first.get("pg_status") == "ok" and first.get("pg_transaction_status") == "ok":
                await self.repository.paybox_client_request_payment_set(
                    item["client_request_payment_id"],
                    item["client_request_id"],
                    first.get("pg_payment_id"),
                    "",
                )
        return "0"
