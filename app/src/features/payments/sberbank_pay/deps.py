from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..sberbank_callback.deps import get_sberbank_client
from ..sberbank_client import SberbankClient
from ..shared_repo import PaymentsRepository
from .service import SberbankPayService


def get_sberbank_pay_service(
    connection: DatabaseConnectionDep,
    sber: Annotated[SberbankClient, Depends(get_sberbank_client)],
) -> SberbankPayService:
    return SberbankPayService(PaymentsRepository(connection=connection), sber)


SberbankPayServiceDep = Annotated[SberbankPayService, Depends(get_sberbank_pay_service)]
