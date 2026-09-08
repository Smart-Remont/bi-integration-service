from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_raw_body
from ..openapi_examples import BIG_NOTIFY_CLIENT_RESPONSE
from .deps import BigNotifyClientServiceDep

router = APIRouter()


@router.post(
    "/big-notify-client",
    summary="Уведомление клиенту",
    description=(
        "**БД:** `big_notify_client`\n\n"
        "Тело — UTF-8 строка без пересериализации. "
        "Ответ с `error.code`; при ошибке HTTP 400."
    ),
    responses=BIG_NOTIFY_CLIENT_RESPONSE,
)
async def big_notify_client(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: BigNotifyClientServiceDep,
) -> JSONResponse:
    raw_body = await read_raw_body(request)
    return await service.big_notify_client(raw_body)


@router.api_route(
    "/big-notify-client",
    methods=["GET", "HEAD", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def big_notify_client_method_not_allowed(
    service: BigNotifyClientServiceDep,
) -> JSONResponse:
    return service.method_not_allowed()
