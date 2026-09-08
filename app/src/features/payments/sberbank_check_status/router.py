from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from src.openapi_helpers import add_cron_route, cron_description

from ..errors import PaymentsDatabaseError
from ..sberbank_client import SberbankClientError
from .deps import SberbankCheckStatusServiceDep

router = APIRouter()


@add_cron_route(
    router,
    "/sberbank-check-payment-status",
    summary="Cron: sberbankCheckPaymentStatusAction",
    description=cron_description(
        "`sberbank_payment_read_for_status` → poll Sber API → update status.",
        php_action="sberbank-check-payment-status",
    ),
)
async def sberbank_check_payment_status(service: SberbankCheckStatusServiceDep) -> Response:
    try:
        return PlainTextResponse(content=await service.poll())
    except (PaymentsDatabaseError, SberbankClientError) as exc:
        return PlainTextResponse(content=getattr(exc, "message", str(exc)), status_code=500)
