from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from .deps import RequestCreateServiceDep

router = APIRouter()


@router.post(
    "/request-create",
    summary="Создание заявки (legacy v1)",
    description=(
        "Legacy-совместимость: **БД:** `ddu__create_request` (старее, чем `ddu__create_request_v2`) "
        "→ `ddu__request_get`. Оставлено тонким прокси на случай, если старый URL ещё вызывается BIG."
    ),
    deprecated=True,
)
async def request_create(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestCreateServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_create(body)
