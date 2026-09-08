from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RemontAvailRepository
from .service import RemontAvailService


def get_remont_avail_service(connection: DatabaseConnectionDep) -> RemontAvailService:
    repository = RemontAvailRepository(connection=connection)
    return RemontAvailService(repository=repository)


RemontAvailServiceDep = Annotated[RemontAvailService, Depends(get_remont_avail_service)]
