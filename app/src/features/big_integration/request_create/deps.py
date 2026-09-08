from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RequestCreateRepository
from .service import RequestCreateService


def get_request_create_service(connection: DatabaseConnectionDep) -> RequestCreateService:
    repository = RequestCreateRepository(connection=connection)
    return RequestCreateService(repository=repository)


RequestCreateServiceDep = Annotated[RequestCreateService, Depends(get_request_create_service)]
