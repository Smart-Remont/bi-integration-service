from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import BigNotifyClientRepository
from .service import BigNotifyClientService


def get_big_notify_client_service(
    connection: DatabaseConnectionDep,
) -> BigNotifyClientService:
    repository = BigNotifyClientRepository(connection=connection)
    return BigNotifyClientService(repository=repository)


BigNotifyClientServiceDep = Annotated[
    BigNotifyClientService,
    Depends(get_big_notify_client_service),
]
