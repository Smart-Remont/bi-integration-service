from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import CrmLegacyRepository
from .service import CrmLegacyService


def get_crm_legacy_service(connection: DatabaseConnectionDep) -> CrmLegacyService:
    return CrmLegacyService(CrmLegacyRepository(connection=connection))


CrmLegacyServiceDep = Annotated[CrmLegacyService, Depends(get_crm_legacy_service)]
