from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import DduExportDatabaseError
from ..responses import ddu_export_error_response, ddu_export_success_response

if TYPE_CHECKING:
    from .repo import DduResidentListRepository


class DduResidentListService(BaseService):
    def __init__(self, repository: "DduResidentListRepository") -> None:
        self.repository = repository

    async def ddu_resident_list(self) -> JSONResponse:
        try:
            rows = await self.repository.ddu_resident_list()
            return ddu_export_success_response(rows)
        except DduExportDatabaseError as exc:
            return ddu_export_error_response(exc.message)
