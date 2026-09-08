from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import LeadsRepository, LeadsSettingsRepository
from .services import LeadsService


def get_leads_service(connection: DatabaseConnectionDep) -> LeadsService:
    return LeadsService(
        LeadsRepository(connection=connection),
        LeadsSettingsRepository(connection=connection),
    )


LeadsServiceDep = Annotated[LeadsService, Depends(get_leads_service)]
