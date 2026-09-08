from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduFlatRemontInfoRepository
from .service import DduFlatRemontInfoService


def get_ddu_flat_remont_info_service(
    connection: DatabaseConnectionDep,
) -> DduFlatRemontInfoService:
    repository = DduFlatRemontInfoRepository(connection=connection)
    return DduFlatRemontInfoService(repository=repository)


DduFlatRemontInfoServiceDep = Annotated[
    DduFlatRemontInfoService,
    Depends(get_ddu_flat_remont_info_service),
]
