from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import ShowroomInfoListRepository
from .service import ShowroomInfoListService


def get_showroom_info_list_service(
    connection: DatabaseConnectionDep,
) -> ShowroomInfoListService:
    return ShowroomInfoListService(ShowroomInfoListRepository(connection=connection))


ShowroomInfoListServiceDep = Annotated[
    ShowroomInfoListService,
    Depends(get_showroom_info_list_service),
]
