from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..auth import DduExportBasicAuthDep
from ..openapi_examples import DDU_EXPORT_FLAT_REMONT_INFO_RESPONSE
from .deps import DduFlatRemontInfoServiceDep

router = APIRouter()


@router.get(
    "/ddu-flat-remont-info",
    summary="Параметры ремонта квартиры по комнатам",
    description=(
        "**БД:** `ddu_flat_remont_info`\n\n"
        "SP возвращает одну строку на пару (комната, параметр); "
        "эндпоинт группирует их в `rooms[].params[]`."
    ),
    responses=DDU_EXPORT_FLAT_REMONT_INFO_RESPONSE,
)
async def ddu_flat_remont_info(
    _: DduExportBasicAuthDep,
    service: DduFlatRemontInfoServiceDep,
    flat_guid: str = Query(default="", description="GUID квартиры"),
) -> JSONResponse:
    return await service.ddu_flat_remont_info(flat_guid)
