from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import WorkersRepository, WorkersSettingsRepository
from .services import WorkersService


def get_workers_service(connection: DatabaseConnectionDep) -> WorkersService:
    return WorkersService(
        WorkersRepository(connection=connection),
        WorkersSettingsRepository(connection=connection),
    )


WorkersServiceDep = Annotated[WorkersService, Depends(get_workers_service)]
