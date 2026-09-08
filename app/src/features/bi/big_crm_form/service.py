import json
from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..responses import bi_error_response, bi_success_response

if TYPE_CHECKING:
    from .repo import BigCrmFormRepository


class BigCrmFormService(BaseService):
    def __init__(self, repository: "BigCrmFormRepository") -> None:
        self.repository = repository

    async def big_crm_form(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.request_from_bigcrm(json.dumps(body))
            return bi_success_response(value)
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
