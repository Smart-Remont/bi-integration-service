from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from .deps import RequestCreateV2ServiceDep

router = APIRouter()


@router.post(
    "/request-create-v2",
    summary="Создание заявки (legacy v2)",
    description=(
        "Legacy-совместимость: та же SP, что `request-create-v3` (`ddu__create_request_v2`), "
        "но ответ без поля `client_request_id`."
    ),
    deprecated=True,
)
async def request_create_v2(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestCreateV2ServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_create_v2(body)
