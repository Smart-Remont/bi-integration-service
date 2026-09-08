from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import REQUEST_CREATE_V3_BODY, REQUEST_CREATE_V3_RESPONSE
from .deps import RequestCreateV3ServiceDep

router = APIRouter()


@router.post(
    "/request-create-v3",
    summary="Создание заявки",
    description=(
        "**БД:** `ddu__create_request_v2` → `ddu__request_get`"
    ),
    openapi_extra=REQUEST_CREATE_V3_BODY,
    responses=REQUEST_CREATE_V3_RESPONSE,
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
