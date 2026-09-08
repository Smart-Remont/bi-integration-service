from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    SR_RENDER_AVAIL_BODY,
    SR_RENDER_AVAIL_RESPONSE,
)
from src.openapi_helpers import integration_controller_description
from .deps import SrRenderAvailServiceDep

router = APIRouter()


@router.post(
    "/sr-render-avail",
    summary="Наличие рендера по списку квартир",
    description=integration_controller_description(
        '**БД:** `bi_render_avail`. Тело: `{"flat_guid": ["...", ...]}`.',
        url_action="sr-render-avail",
        php_method="srRenderAvailAction",
    ),
    openapi_extra=SR_RENDER_AVAIL_BODY,
    responses=SR_RENDER_AVAIL_RESPONSE,
)
async def sr_render_avail(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: SrRenderAvailServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.sr_render_avail(body)
