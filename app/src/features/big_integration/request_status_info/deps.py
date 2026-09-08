from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RequestStatusInfoRepository
from .service import RequestStatusInfoService


def get_request_status_info_service(
    connection: DatabaseConnectionDep,
) -> RequestStatusInfoService:
    repository = RequestStatusInfoRepository(connection=connection)
    return RequestStatusInfoService(repository=repository)


RequestStatusInfoServiceDep = Annotated[
    RequestStatusInfoService,
    Depends(get_request_status_info_service),
]
