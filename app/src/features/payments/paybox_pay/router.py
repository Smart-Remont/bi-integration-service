from fastapi import APIRouter, Request
from fastapi.responses import Response

from .deps import PayboxPayServiceDep

router = APIRouter()


@router.api_route(
    "/paybox/mode/{mode}",
    methods=["GET", "POST"],
    summary="Paybox pay (legacy multi-mode)",
    description="Modes: ``init``, ``status`` (cron). Disabled unless ``PAYBOX_ENABLED=true``.",
)
@router.api_route(
    "/paybox/mode/{mode}/request/{request_hash}/payment/{payment_hash}",
    methods=["GET", "POST"],
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
