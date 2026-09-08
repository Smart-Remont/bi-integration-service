from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object_ru
from ..openapi_examples import (
    REQUEST_CONSTRUCTIVES_BODY,
    REQUEST_CONSTRUCTIVES_RESPONSE,
)
from ..responses import big_integration_error_response
from .deps import RequestConstructivesServiceDep

router = APIRouter()

_METHOD_NOT_ALLOWED = "Неподдерживаемый метод"


@router.post(
    "/request-constructives",
    summary="Материалы и наполнение",
    description=(
        "**БД:** `ddu_client_material__read`, `ddu_client_filling__read`, "
        "`ddu_request_full_info`\n\n"
        "Поле `characteristic_json` в наполнении разбирается из строки в объект."
    ),
    openapi_extra=REQUEST_CONSTRUCTIVES_BODY,
    responses=REQUEST_CONSTRUCTIVES_RESPONSE,
)
async def request_constructives(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RequestConstructivesServiceDep,
) -> JSONResponse:
    body = await read_json_object_ru(request)
    if isinstance(body, JSONResponse):
        return body

    return await service.request_constructives(body)


@router.api_route(
    "/request-constructives",
    methods=["GET", "HEAD", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def request_constructives_method_not_allowed() -> JSONResponse:
    return big_integration_error_response(
        _METHOD_NOT_ALLOWED,
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    )
