import json
from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import BigCrmFormRepository


class BigCrmFormService(BaseService):
    def __init__(self, repository: "BigCrmFormRepository") -> None:
        self.repository = repository

    async def big_crm_form(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.request_from_bigcrm(json.dumps(body))
            return legacy_bi_success_response(value)
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
