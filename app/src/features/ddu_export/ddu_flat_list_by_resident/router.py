from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..auth import DduExportBasicAuthDep
from ..openapi_examples import DDU_EXPORT_PARAM_RESPONSE
from .deps import DduFlatListByResidentServiceDep

router = APIRouter()


@router.get(
    "/ddu-flat-list-by-resident",
    summary="Квартиры жителя по GUID",
    description="**БД:** `ddu_flat_list_by_resident`",
    responses=DDU_EXPORT_PARAM_RESPONSE,
)
async def ddu_flat_list_by_resident(
    _: DduExportBasicAuthDep,
    service: DduFlatListByResidentServiceDep,
    resident_guid: str = Query(default="", description="GUID жителя"),
) -> JSONResponse:
    return await service.ddu_flat_list_by_resident(resident_guid)
