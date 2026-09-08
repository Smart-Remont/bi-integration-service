from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.openapi_helpers import legacy_client_path

from .deps import CloudPaymentsServiceDep

router = APIRouter()

_DESC = (
    "CloudPayments webhook: urlencoded body (`Data`, `InvoiceId`, `Amount`, `TransactionId`). "
    "Modes: `check`, `pay`, `fail`. **БД:** `client.cloud_payments_pay`.\n"
    "POST также принимается (скрыт)."
    + legacy_client_path("cp-response/mode/{mode}")
)


@router.post(
    "/cloudpayments/mode/{mode}",
    summary="cpResponseAction",
    description=_DESC,
)
@router.get("/cloudpayments/mode/{mode}", include_in_schema=False)
async def cloud_payments(
    mode: str,
    request: Request,
    service: CloudPaymentsServiceDep,
) -> JSONResponse:
    return await service.handle(mode, request)
