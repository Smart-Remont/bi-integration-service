from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import KaspiRepository
from .service import KaspiService


def get_kaspi_service(connection: DatabaseConnectionDep) -> KaspiService:
    return KaspiService(KaspiRepository(connection=connection))


KaspiServiceDep = Annotated[KaspiService, Depends(get_kaspi_service)]
