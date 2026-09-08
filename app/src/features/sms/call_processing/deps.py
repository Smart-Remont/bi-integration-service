from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import CallProcessingRepository
from .service import CallProcessingService


def get_call_processing_service(connection: DatabaseConnectionDep) -> CallProcessingService:
    repository = CallProcessingRepository(connection=connection)
    return CallProcessingService(repository=repository)


CallProcessingServiceDep = Annotated[CallProcessingService, Depends(get_call_processing_service)]
