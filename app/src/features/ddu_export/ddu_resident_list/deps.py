from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduResidentListRepository
from .service import DduResidentListService


def get_ddu_resident_list_service(
    connection: DatabaseConnectionDep,
) -> DduResidentListService:
    repository = DduResidentListRepository(connection=connection)
    return DduResidentListService(repository=repository)


DduResidentListServiceDep = Annotated[
    DduResidentListService,
    Depends(get_ddu_resident_list_service),
]
