from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..http import read_json_object
from ..openapi_examples import LEGACY_BI_RESPONSE
from .deps import SrRemontAvailServiceDep

router = APIRouter()


@router.post(
    "/sr-remont-avail",
    summary="Наличие ЧО по списку блоков",
    description='**БД:** `bi_cho_avail`. Тело: `{"realEstateUUIDs": ["...", ...]}`.',
    responses=LEGACY_BI_RESPONSE,
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
