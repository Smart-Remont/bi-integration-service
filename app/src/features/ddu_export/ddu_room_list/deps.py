from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduRoomListRepository
from .service import DduRoomListService


def get_ddu_room_list_service(
    connection: DatabaseConnectionDep,
) -> DduRoomListService:
    repository = DduRoomListRepository(connection=connection)
    return DduRoomListService(repository=repository)


DduRoomListServiceDep = Annotated[
    DduRoomListService,
    Depends(get_ddu_room_list_service),
]
