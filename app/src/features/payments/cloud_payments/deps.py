from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import CloudPaymentsRepository
from .service import CloudPaymentsService


def get_cloud_payments_service(connection: DatabaseConnectionDep) -> CloudPaymentsService:
    return CloudPaymentsService(CloudPaymentsRepository(connection=connection))


CloudPaymentsServiceDep = Annotated[CloudPaymentsService, Depends(get_cloud_payments_service)]
