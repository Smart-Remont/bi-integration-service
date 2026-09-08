from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import SrRequestListServiceDep

router = APIRouter()


@router.post(
    "/sr-request-list",
    summary="Список заявок BI по квартире/ИИН",
    description="**БД:** `bi_client_request_list`",
    responses=LEGACY_BI_RESPONSE,
)
async def sr_request_list(
    request: Request,
    _: BigIntegrationBasicAuthDep,
    service: SrRequestListServiceDep,
) -> JSONResponse:
    body = await read_json_object(request)
    if isinstance(body, JSONResponse):
        return body
    return await service.sr_request_list(body)
