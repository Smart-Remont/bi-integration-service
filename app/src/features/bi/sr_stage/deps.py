from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrStageRepository
from .service import SrStageService


def get_sr_stage_service(connection: DatabaseConnectionDep) -> SrStageService:
    repository = SrStageRepository(connection=connection)
    return SrStageService(repository=repository)


SrStageServiceDep = Annotated[SrStageService, Depends(get_sr_stage_service)]
