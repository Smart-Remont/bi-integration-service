from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from .deps import RequestCreateV3ServiceDep

router = APIRouter()


@router.post(
    "/request-create-v3",
    summary="Создать заявку ДДУ",
    description=(
        "Создаёт новую заявку (`sp: rest.ddu__create_request_v2`) и возвращает её состояние "
        "(`rest.ddu__request_get`). Валидация полей — внутри stored function; при ошибке — "
        "`error.message` из PostgreSQL."
    ),
)
async def request_create_v3(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestCreateV3ServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_create_v3(body)
