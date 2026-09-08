from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduFlatListByResidentRepository
from .service import DduFlatListByResidentService


def get_ddu_flat_list_by_resident_service(
    connection: DatabaseConnectionDep,
) -> DduFlatListByResidentService:
    repository = DduFlatListByResidentRepository(connection=connection)
    return DduFlatListByResidentService(repository=repository)


DduFlatListByResidentServiceDep = Annotated[
    DduFlatListByResidentService,
    Depends(get_ddu_flat_list_by_resident_service),
]
