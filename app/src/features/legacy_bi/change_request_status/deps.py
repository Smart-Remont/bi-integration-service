from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import ChangeRequestStatusRepository
from .service import ChangeRequestStatusService


def get_change_request_status_service(connection: DatabaseConnectionDep) -> ChangeRequestStatusService:
    repository = ChangeRequestStatusRepository(connection=connection)
    return ChangeRequestStatusService(repository=repository)


ChangeRequestStatusServiceDep = Annotated[ChangeRequestStatusService, Depends(get_change_request_status_service)]
