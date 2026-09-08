from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RequestEventRepository
from .service import RequestEventService


def get_request_event_service(connection: DatabaseConnectionDep) -> RequestEventService:
    repository = RequestEventRepository(connection=connection)
    return RequestEventService(repository=repository)


RequestEventServiceDep = Annotated[RequestEventService, Depends(get_request_event_service)]
