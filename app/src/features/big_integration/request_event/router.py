from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from ..openapi_examples import REQUEST_EVENT_V3_BODY, REQUEST_EVENT_V3_RESPONSE
from .deps import RequestEventServiceDep

router = APIRouter()


@router.post(
    "/request-event",
    summary="Событие по заявке (legacy v1)",
    description=(
        "Legacy-совместимость: **БД:** `ddu__request_event` (старее, чем `ddu__request_event_v3`) "
        "→ `ddu__request_get`, ответ без `client_request_id`."
    ),
    deprecated=True,
    openapi_extra=REQUEST_EVENT_V3_BODY,
    responses=REQUEST_EVENT_V3_RESPONSE,
)
async def request_event(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestEventServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_event(body)
