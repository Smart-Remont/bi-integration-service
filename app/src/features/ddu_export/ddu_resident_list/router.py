from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import DduExportBasicAuthDep
from ..openapi_examples import DDU_EXPORT_LIST_RESPONSE
from .deps import DduResidentListServiceDep

router = APIRouter()


@router.get(
    "/ddu-resident-list",
    summary="Список жителей ДДУ",
    description="**БД:** `ddu_resident_list`",
    responses=DDU_EXPORT_LIST_RESPONSE,
)
async def ddu_resident_list(
    _: DduExportBasicAuthDep,
    service: DduResidentListServiceDep,
) -> JSONResponse:
    return await service.ddu_resident_list()
