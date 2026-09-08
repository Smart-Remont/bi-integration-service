from fastapi import APIRouter, Request
from fastapi.responses import Response

from ..sberbank_callback.deps import merge_request_params
from .deps import SberbankPayServiceDep

router = APIRouter()


@router.api_route(
    "/sberbank-pay/mode/{mode}",
    methods=["GET", "POST"],
    summary="Sberbank pay (legacy multi-mode)",
    description="Modes: ``register``, ``status`` (order_id/order_num query), ``postlink``.",
)
@router.api_route(
    "/sberbank-pay/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    methods=["GET", "POST"],
    include_in_schema=True,
)
async def sberbank_pay(
    mode: str,
    request: Request,
    service: SberbankPayServiceDep,
    request_hash: str | None = None,
    payment_hash: str | None = None,
) -> Response:
    params = await merge_request_params(request)
    base_url = str(request.base_url).rstrip("/")
    return await service.handle(mode, request_hash, payment_hash, base_url, params)
