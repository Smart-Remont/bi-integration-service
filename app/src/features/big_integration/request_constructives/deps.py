import json
from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import RequestConstructivesRepository
from .service import RequestConstructivesService


def get_request_constructives_service(
    connection: DatabaseConnectionDep,
) -> RequestConstructivesService:
    repository = RequestConstructivesRepository(connection=connection)
    return RequestConstructivesService(repository=repository)


RequestConstructivesServiceDep = Annotated[
    RequestConstructivesService,
    Depends(get_request_constructives_service),
]
