from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..forte_client import ForteClient
from ..settings_repo import PaymentSettingsRepository
from ..shared_repo import PaymentsRepository
from .service import FortePayService


def get_forte_client() -> ForteClient:
    return ForteClient()


def get_forte_pay_service(
    connection: DatabaseConnectionDep,
    forte: Annotated[ForteClient, Depends(get_forte_client)],
) -> FortePayService:
    return FortePayService(
        PaymentsRepository(connection=connection),
        PaymentSettingsRepository(connection=connection),
        forte,
    )


FortePayServiceDep = Annotated[FortePayService, Depends(get_forte_pay_service)]
