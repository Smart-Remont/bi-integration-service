from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from ..sberbank_callback.deps import get_sberbank_client
from ..sberbank_client import SberbankClient
from ..shared_repo import PaymentsRepository
from .service import SberbankCheckStatusService


def get_sberbank_check_status_service(
    connection: DatabaseConnectionDep,
    sber: Annotated[SberbankClient, Depends(get_sberbank_client)],
) -> SberbankCheckStatusService:
    return SberbankCheckStatusService(PaymentsRepository(connection=connection), sber)


SberbankCheckStatusServiceDep = Annotated[
    SberbankCheckStatusService,
    Depends(get_sberbank_check_status_service),
]
