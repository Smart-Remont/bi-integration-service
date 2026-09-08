from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import bi_error_response, bi_success_response

if TYPE_CHECKING:
    from .repo import SrResidentReportRepository


class SrResidentReportService(BaseService):
    def __init__(self, repository: "SrResidentReportRepository") -> None:
        self.repository = repository

    async def sr_resident_report(self) -> JSONResponse:
        try:
            value = await self.repository.sr_resident_report()
            return bi_success_response(parse_scalar_json(value))
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
