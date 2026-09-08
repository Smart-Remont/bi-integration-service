from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.openapi_helpers import legacy_integration_path

from ..sberbank_callback.deps import merge_request_params
from .deps import FortePayServiceDep

router = APIRouter()

_DESC = (
    "Modes: `register`, `status` (cron), callbacks. Write SP `forte_*` may be absent in DB.\n"
    "POST также принимается (скрыт)."
    + legacy_integration_path("forte-pay/mode/{mode}")
)


@router.get("/forte-pay/mode/{mode}", summary="fortePayAction", description=_DESC)
@router.post("/forte-pay/mode/{mode}", include_in_schema=False)
@router.get(
    "/forte-pay/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    summary="fortePayAction — path с hash",
    description=_DESC,
)
@router.post(
    "/forte-pay/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    include_in_schema=False,
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
