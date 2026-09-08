from fastapi import APIRouter, Request
from fastapi.responses import Response

from ..sberbank_callback.deps import merge_request_params
from .deps import FortePayServiceDep

router = APIRouter()


@router.api_route(
    "/forte-pay/mode/{mode}",
    methods=["GET", "POST"],
    summary="Forte pay (legacy multi-mode)",
    description=(
        "Modes: ``register``, ``status`` (cron), ``on_approve/on_cancel/on_decline`` callbacks. "
        "Write SP ``forte_transaction_set`` / ``forte_client_request_payment_set`` may be absent in DB."
    ),
)
@router.api_route(
    "/forte-pay/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    methods=["GET", "POST"],
)
async def forte_pay(
    mode: str,
    request: Request,
    service: FortePayServiceDep,
    request_hash: str | None = None,
    payment_hash: str | None = None,
) -> Response:
    params = await merge_request_params(request)
    base_url = str(request.base_url).rstrip("/")
    return await service.handle(mode, request_hash, payment_hash, base_url, params)
