from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import SrRenderServiceDep

router = APIRouter()


@router.post(
    "/sr-render",
    summary="Ракурсы рендера по квартире",
    description="**БД:** `bi_rakurs_list_v2`",
    responses=LEGACY_BI_RESPONSE,
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
