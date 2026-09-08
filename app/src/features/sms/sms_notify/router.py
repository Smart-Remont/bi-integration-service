from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClientError
from .deps import SmsNotifyServiceDep

router = APIRouter()


@router.api_route(
    "/sms-notify",
    methods=["GET", "POST"],
    summary="Отправка notify-SMS из очереди",
    description=(
        "Cron: `notify.sms_notify__read` → Kcell Hermes → `notify.sms_notify_result__set`. "
        "Пустая очередь → `No messages to send.`"
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
