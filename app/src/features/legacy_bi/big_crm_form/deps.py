from typing import Annotated

from fastapi import Depends
from src.database.deps import DatabaseConnectionDep

from .repo import BigCrmFormRepository
from .service import BigCrmFormService


def get_big_crm_form_service(connection: DatabaseConnectionDep) -> BigCrmFormService:
    repository = BigCrmFormRepository(connection=connection)
    return BigCrmFormService(repository=repository)


BigCrmFormServiceDep = Annotated[BigCrmFormService, Depends(get_big_crm_form_service)]
