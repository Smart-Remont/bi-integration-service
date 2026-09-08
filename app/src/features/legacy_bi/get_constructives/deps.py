from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import GetConstructivesRepository
from .service import GetConstructivesService


def get_get_constructives_service(connection: DatabaseConnectionDep) -> GetConstructivesService:
    repository = GetConstructivesRepository(connection=connection)
    return GetConstructivesService(repository=repository)


GetConstructivesServiceDep = Annotated[GetConstructivesService, Depends(get_get_constructives_service)]
