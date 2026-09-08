from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.openapi_helpers import legacy_integration_path

from .deps import PayboxPayServiceDep

router = APIRouter()

_DESC = (
    "Modes: `init`, `status` (cron). Disabled unless `PAYBOX_ENABLED=true`.\n"
    "POST также принимается (скрыт)."
    + legacy_integration_path("paybox/mode/{mode}")
)


@router.get("/paybox/mode/{mode}", summary="payboxPayAction", description=_DESC)
@router.post("/paybox/mode/{mode}", include_in_schema=False)
@router.get(
    "/paybox/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    summary="payboxPayAction — path с hash",
    description=_DESC,
)
@router.post(
    "/paybox/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    include_in_schema=False,
)
async def paybox_pay(
    mode: str,
    request: Request,
    service: PayboxPayServiceDep,
    request_hash: str | None = None,
    payment_hash: str | None = None,
) -> Response:
    base_url = str(request.base_url).rstrip("/")
    return await service.handle(mode, request_hash, payment_hash, base_url)
