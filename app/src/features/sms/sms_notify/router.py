from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from src.openapi_helpers import add_cron_route, cron_description

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClientError
from .deps import SmsNotifyServiceDep

router = APIRouter()


@add_cron_route(
    router,
    "/sms-notify",
    summary="Cron: smsNotifyAction — notify SMS",
    description=cron_description(
        "`notify.sms_notify__read` → Kcell Hermes → `notify.sms_notify_result__set`. "
        "Пустая очередь → `No messages to send.`",
        php_action="sms-notify",
    ),
)
async def sms_notify(service: SmsNotifyServiceDep) -> Response:
    try:
        body = await service.process_notify_queue()
        return PlainTextResponse(content=body)
    except KcellClientError as exc:
        return PlainTextResponse(content=exc.message, status_code=503)
    except SmsDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)
