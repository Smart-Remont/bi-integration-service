from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RequestInfoRepository
from .service import RequestInfoService


def get_request_info_service(
    connection: DatabaseConnectionDep,
) -> RequestInfoService:
    repository = RequestInfoRepository(connection=connection)
    return RequestInfoService(repository=repository)


RequestInfoServiceDep = Annotated[
    RequestInfoService,
    Depends(get_request_info_service),
]
