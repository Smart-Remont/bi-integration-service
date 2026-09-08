from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import SrShowroomReportRepository


class SrShowroomReportService(BaseService):
    def __init__(self, repository: "SrShowroomReportRepository") -> None:
        self.repository = repository

    async def sr_showroom_report(self) -> JSONResponse:
        try:
            value = await self.repository.sr_showroom_report()
            return legacy_bi_success_response(parse_scalar_json(value))
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
