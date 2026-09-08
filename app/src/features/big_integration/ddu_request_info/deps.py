from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import DduRequestInfoRepository
from .service import DduRequestInfoService


def get_ddu_request_info_service(
    connection: DatabaseConnectionDep,
) -> DduRequestInfoService:
    repository = DduRequestInfoRepository(connection=connection)
    return DduRequestInfoService(repository=repository)


DduRequestInfoServiceDep = Annotated[
    DduRequestInfoService,
    Depends(get_ddu_request_info_service),
]
