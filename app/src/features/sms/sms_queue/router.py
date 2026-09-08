from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClientError
from .deps import SmsQueueServiceDep

router = APIRouter()


@router.api_route(
    "/sms",
    methods=["GET", "POST"],
    summary="Отправка SMS из очереди client",
    description=(
        "Cron: `client.sms_number_read` → Kcell Hermes `/batches` (по 200 сообщений) "
        "→ `client.sms_set_result`. Без auth (как legacy `smsAction`). Ответ: `0`."
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
