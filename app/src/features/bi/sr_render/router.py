from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import (
    SR_RENDER_BODY,
    SR_RENDER_RESPONSE,
)
from src.openapi_helpers import integration_controller_description
from .deps import SrRenderServiceDep

router = APIRouter()


@router.post(
    "/sr-render",
    summary="Ракурсы рендера по квартире",
    description=integration_controller_description(
        "**БД:** `bi_rakurs_list_v2`",
        url_action="sr-render",
        php_method="srRenderAction",
    ),
    openapi_extra=SR_RENDER_BODY,
    responses=SR_RENDER_RESPONSE,
)
async def sr_render(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: SrRenderServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.sr_render(body)
