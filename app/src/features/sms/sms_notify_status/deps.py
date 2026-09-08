from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..kcell_client import KcellClient
from ..sms_queue.deps import get_kcell_client
from .repo import SmsNotifyStatusRepository
from .service import SmsNotifyStatusService


def get_sms_notify_status_service(
    connection: DatabaseConnectionDep,
    kcell: Annotated[KcellClient, Depends(get_kcell_client)],
) -> SmsNotifyStatusService:
    repository = SmsNotifyStatusRepository(connection=connection)
    return SmsNotifyStatusService(repository=repository, kcell=kcell)


SmsNotifyStatusServiceDep = Annotated[SmsNotifyStatusService, Depends(get_sms_notify_status_service)]
