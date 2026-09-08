from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import BigappFormRepository
from .service import BigappFormService


def get_bigapp_form_service(connection: DatabaseConnectionDep) -> BigappFormService:
    repository = BigappFormRepository(connection=connection)
    return BigappFormService(repository=repository)


BigappFormServiceDep = Annotated[BigappFormService, Depends(get_bigapp_form_service)]
