from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from .deps import RequestEventV3ServiceDep

router = APIRouter()


@router.post(
    "/request-event-v3",
    summary="Обновить статус заявки ДДУ (событие)",
    description=(
        "Принимает событие по существующей заявке (`sp: rest.ddu__request_event_v3`) и "
        "возвращает актуальное состояние заявки (`rest.ddu__request_get`). Валидация полей — "
        "внутри stored function; при ошибке — `error.message` из PostgreSQL."
    ),
)
async def request_event_v3(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestEventV3ServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_event_v3(body)
