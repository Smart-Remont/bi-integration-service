from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import DduExportBasicAuthDep
from ..openapi_examples import DDU_EXPORT_ROOM_TYPE_LIST_RESPONSE
from .deps import DduRoomTypeListServiceDep

router = APIRouter()


@router.get(
    "/ddu-room-type-list",
    summary="Справочник типов комнат",
    description="**БД:** `ddu_room_type_list`",
    responses=DDU_EXPORT_ROOM_TYPE_LIST_RESPONSE,
)
async def ddu_room_type_list(
    _: DduExportBasicAuthDep,
    service: DduRoomTypeListServiceDep,
) -> JSONResponse:
    return await service.ddu_room_type_list()
