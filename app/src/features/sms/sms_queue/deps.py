from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..kcell_client import KcellClient
from .repo import SmsQueueRepository
from .service import SmsQueueService


def get_kcell_client() -> KcellClient:
    return KcellClient()


def get_sms_queue_service(
    connection: DatabaseConnectionDep,
    kcell: Annotated[KcellClient, Depends(get_kcell_client)],
) -> SmsQueueService:
    repository = SmsQueueRepository(connection=connection)
    return SmsQueueService(repository=repository, kcell=kcell)


SmsQueueServiceDep = Annotated[SmsQueueService, Depends(get_sms_queue_service)]
