from typing import Annotated

from fastapi import Depends
from src.config import app_config
from src.database.deps import DatabaseConnectionDep

from .ff.client import FactoringClient
from .ff.repo import FactoringRepository
from .ff.service import FactoringService


def get_factoring_service(connection: DatabaseConnectionDep) -> FactoringService:
    repository = FactoringRepository(connection=connection)
    client = FactoringClient()
    return FactoringService(
        repository=repository,
        client=client,
        app_env=app_config.env,
    )


FactoringServiceDep = Annotated[FactoringService, Depends(get_factoring_service)]
