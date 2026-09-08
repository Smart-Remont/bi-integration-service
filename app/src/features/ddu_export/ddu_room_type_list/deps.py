from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduRoomTypeListRepository
from .service import DduRoomTypeListService


def get_ddu_room_type_list_service(
    connection: DatabaseConnectionDep,
) -> DduRoomTypeListService:
    repository = DduRoomTypeListRepository(connection=connection)
    return DduRoomTypeListService(repository=repository)


DduRoomTypeListServiceDep = Annotated[
    DduRoomTypeListService,
    Depends(get_ddu_room_type_list_service),
]
