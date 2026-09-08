from typing import Annotated

from fastapi import Depends, Request
from src.database.deps import DatabaseConnectionDep

from ..sberbank_client import SberbankClient
from ..shared_repo import PaymentsRepository
from .service import SberbankCallbackService


def get_sberbank_client() -> SberbankClient:
    return SberbankClient()


def get_sberbank_callback_service(
    connection: DatabaseConnectionDep,
    sber: Annotated[SberbankClient, Depends(get_sberbank_client)],
) -> SberbankCallbackService:
    return SberbankCallbackService(PaymentsRepository(connection=connection), sber)


SberbankCallbackServiceDep = Annotated[
    SberbankCallbackService,
    Depends(get_sberbank_callback_service),
]


async def merge_request_params(request: Request) -> dict[str, object]:
    params: dict[str, object] = dict(request.query_params)
    if request.method == "POST":
        form = await request.form()
        params.update({k: v for k, v in form.items()})
    return params
