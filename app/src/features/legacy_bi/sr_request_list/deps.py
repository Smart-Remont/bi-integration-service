from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import SrRequestListRepository
from .service import SrRequestListService


def get_sr_request_list_service(connection: DatabaseConnectionDep) -> SrRequestListService:
    repository = SrRequestListRepository(connection=connection)
    return SrRequestListService(repository=repository)


SrRequestListServiceDep = Annotated[SrRequestListService, Depends(get_sr_request_list_service)]
