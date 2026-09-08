from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduFlatInfoRepository
from .service import DduFlatInfoService


def get_ddu_flat_info_service(
    connection: DatabaseConnectionDep,
) -> DduFlatInfoService:
    repository = DduFlatInfoRepository(connection=connection)
    return DduFlatInfoService(repository=repository)


DduFlatInfoServiceDep = Annotated[
    DduFlatInfoService,
    Depends(get_ddu_flat_info_service),
]
