from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RequestCreateV2Repository
from .service import RequestCreateV2Service


def get_request_create_v2_service(connection: DatabaseConnectionDep) -> RequestCreateV2Service:
    repository = RequestCreateV2Repository(connection=connection)
    return RequestCreateV2Service(repository=repository)


RequestCreateV2ServiceDep = Annotated[RequestCreateV2Service, Depends(get_request_create_v2_service)]
