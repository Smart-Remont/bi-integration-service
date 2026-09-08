from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from src.openapi_helpers import add_cron_route, cron_description

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClientError
from .deps import SmsQueueServiceDep

router = APIRouter()


@add_cron_route(
    router,
    "/sms",
    summary="Cron: smsAction — очередь SMS client",
    description=cron_description(
        "`client.sms_number_read` → Kcell Hermes `/batches` (до 200) → `client.sms_set_result`.",
        php_action="sms",
    ),
)
async def sms_queue(service: SmsQueueServiceDep) -> Response:
    try:
        body = await service.process_queue()
        return PlainTextResponse(content=body)
    except KcellClientError as exc:
        return PlainTextResponse(content=exc.message, status_code=503)
    except SmsDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)
