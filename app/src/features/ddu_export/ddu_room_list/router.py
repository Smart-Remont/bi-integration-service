from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..auth import DduExportBasicAuthDep
from ..openapi_examples import DDU_EXPORT_ROOM_LIST_RESPONSE
from .deps import DduRoomListServiceDep

router = APIRouter()


@router.get(
    "/ddu-room-list",
    summary="Справочник комнат",
    description="**БД:** `ddu_room_list`",
    responses=DDU_EXPORT_ROOM_LIST_RESPONSE,
)
async def ddu_room_list(
    _: DduExportBasicAuthDep,
    service: DduRoomListServiceDep,
) -> JSONResponse:
    return await service.ddu_room_list()
