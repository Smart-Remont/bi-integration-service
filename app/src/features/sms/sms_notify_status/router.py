from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from src.openapi_helpers import add_cron_route, cron_description

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClientError
from .deps import SmsNotifyStatusServiceDep

router = APIRouter()


@add_cron_route(
    router,
    "/sms-notify-status",
    summary="Cron: smsNotifyStatusAction — poll batch Kcell",
    description=cron_description(
        "`notify.sms_notify_batch__read` → Kcell batch API → `notify.sms_notify_status__set`. "
        "Пусто → `No batches to check.`",
        php_action="sms-notify-status",
    ),
)
async def sms_notify_status(service: SmsNotifyStatusServiceDep) -> Response:
    try:
        body = await service.poll_batch_statuses()
        return PlainTextResponse(content=body)
    except KcellClientError as exc:
        return PlainTextResponse(content=exc.message, status_code=503)
    except SmsDatabaseError as exc:
        return PlainTextResponse(content=exc.message, status_code=500)
