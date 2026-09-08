from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..auth import BigIntegrationBasicAuthDep
from ..openapi_examples import REQUEST_INFO_RESPONSE
from .deps import DduFlatInfoServiceDep

router = APIRouter()


@router.get(
    "/ddu-flat-info",
    summary="Квартира по GUID",
    description="**БД:** `ddu_flat_info`",
    responses=REQUEST_INFO_RESPONSE,
)
async def ddu_flat_info(
    _: BigIntegrationBasicAuthDep,
    service: DduFlatInfoServiceDep,
    flat_guid: str = Query(default="", description="GUID квартиры"),
) -> JSONResponse:
    return await service.ddu_flat_info(flat_guid)
