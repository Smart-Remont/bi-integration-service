from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..paybox_client import PayboxClient
from ..settings_repo import PaymentSettingsRepository
from ..shared_repo import PaymentsRepository
from .service import PayboxPayService


def get_paybox_client() -> PayboxClient:
    return PayboxClient()


def get_paybox_pay_service(
    connection: DatabaseConnectionDep,
    paybox: Annotated[PayboxClient, Depends(get_paybox_client)],
) -> PayboxPayService:
    return PayboxPayService(
        PaymentsRepository(connection=connection),
        PaymentSettingsRepository(connection=connection),
        paybox,
    )


PayboxPayServiceDep = Annotated[PayboxPayService, Depends(get_paybox_pay_service)]
