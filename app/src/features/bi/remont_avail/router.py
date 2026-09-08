from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    REMONT_AVAIL_BODY,
    REMONT_AVAIL_RESPONSE,
)
from src.openapi_helpers import integration_controller_description
from .deps import RemontAvailServiceDep

router = APIRouter()


@router.post(
    "/remont-avail",
    summary="Наличие ремонта по квартире/жителю",
    description=integration_controller_description(
        '**БД:** `bi_remont_avail`. Тело: `{"flat_guid"?, "resident_guid"?, "flat_num"?}`.',
        url_action="remont-avail",
        php_method="remontAvailAction",
    ),
    openapi_extra=REMONT_AVAIL_BODY,
    responses=REMONT_AVAIL_RESPONSE,
)
async def remont_avail(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: RemontAvailServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.remont_avail(body)
