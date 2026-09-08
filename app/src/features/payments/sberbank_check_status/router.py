from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from ..errors import PaymentsDatabaseError
from ..sberbank_client import SberbankClientError
from .deps import SberbankCheckStatusServiceDep

router = APIRouter()


@router.api_route(
    "/sberbank-check-payment-status",
    methods=["GET", "POST"],
    summary="Cron: poll Sber payment statuses",
    description="Legacy ``sberbankCheckPaymentStatusAction`` → ``sberbank_payment_read_for_status``.",
)
async def sberbank_check_payment_status(service: SberbankCheckStatusServiceDep) -> Response:
    try:
        return PlainTextResponse(content=await service.poll())
    except (PaymentsDatabaseError, SberbankClientError) as exc:
        return PlainTextResponse(content=getattr(exc, "message", str(exc)), status_code=500)
