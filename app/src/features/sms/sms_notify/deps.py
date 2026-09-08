from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..kcell_client import KcellClient
from ..sms_queue.deps import get_kcell_client
from .repo import SmsNotifyRepository
from .service import SmsNotifyService


def get_sms_notify_service(
    connection: DatabaseConnectionDep,
    kcell: Annotated[KcellClient, Depends(get_kcell_client)],
) -> SmsNotifyService:
    repository = SmsNotifyRepository(connection=connection)
    return SmsNotifyService(repository=repository, kcell=kcell)


SmsNotifyServiceDep = Annotated[SmsNotifyService, Depends(get_sms_notify_service)]
