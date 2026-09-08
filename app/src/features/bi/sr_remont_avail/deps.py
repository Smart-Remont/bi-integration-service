from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrRemontAvailRepository
from .service import SrRemontAvailService


def get_sr_remont_avail_service(connection: DatabaseConnectionDep) -> SrRemontAvailService:
    repository = SrRemontAvailRepository(connection=connection)
    return SrRemontAvailService(repository=repository)


SrRemontAvailServiceDep = Annotated[SrRemontAvailService, Depends(get_sr_remont_avail_service)]
