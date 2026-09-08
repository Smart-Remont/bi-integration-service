from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClientError
from .deps import SmsNotifyStatusServiceDep

router = APIRouter()


@router.api_route(
    "/sms-notify-status",
    methods=["GET", "POST"],
    summary="Poll статусов Kcell batch для notify",
    description=(
        "Cron: `notify.sms_notify_batch__read` → Kcell batch API → "
        "`notify.sms_notify_status__set`. Пусто → `No batches to check.`"
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
