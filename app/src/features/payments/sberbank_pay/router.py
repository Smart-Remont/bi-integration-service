from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.openapi_helpers import legacy_integration_path

from ..sberbank_callback.deps import merge_request_params
from .deps import SberbankPayServiceDep

router = APIRouter()

_PAY_DESC = (
    "Modes: `register`, `status` (query order_id/order_num), `postlink`.\n"
    "POST также принимается (скрыт из OpenAPI)."
    + legacy_integration_path("sberbank-pay/mode/{mode}")
)


@router.get(
    "/sberbank-pay/mode/{mode}",
    summary="sberbankPayAction — redirect/register Sber",
    description=_PAY_DESC,
)
@router.post("/sberbank-pay/mode/{mode}", include_in_schema=False)
@router.get(
    "/sberbank-pay/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    summary="sberbankPayAction — с hash в path",
    description=_PAY_DESC,
    include_in_schema=True,
)
@router.post(
    "/sberbank-pay/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    include_in_schema=False,
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
