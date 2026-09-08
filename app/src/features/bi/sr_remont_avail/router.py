from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    SR_REMONT_AVAIL_BODY,
    SR_REMONT_AVAIL_RESPONSE,
)
from src.openapi_helpers import integration_controller_description
from .deps import SrRemontAvailServiceDep

router = APIRouter()


@router.post(
    "/sr-remont-avail",
    summary="Наличие ЧО по списку блоков",
    description=integration_controller_description(
        '**БД:** `bi_cho_avail`. Тело: `{"realEstateUUIDs": ["...", ...]}`.',
        url_action="sr-remont-avail",
        php_method="srRemontAvailAction",
    ),
    openapi_extra=SR_REMONT_AVAIL_BODY,
    responses=SR_REMONT_AVAIL_RESPONSE,
)
async def sr_remont_avail(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: SrRemontAvailServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.sr_remont_avail(body)
