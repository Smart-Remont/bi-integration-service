from typing import TYPE_CHECKING

from fastapi import status
from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import DduExportDatabaseError
from ..responses import ddu_export_error_response, ddu_export_success_response

if TYPE_CHECKING:
    from .repo import DduFlatListByResidentRepository

_RESIDENT_GUID_REQUIRED_RU = 'Параметр resident_guid обязателен'


class DduFlatListByResidentService(BaseService):
    def __init__(self, repository: "DduFlatListByResidentRepository") -> None:
        self.repository = repository

    async def ddu_flat_list_by_resident(self, resident_guid: str) -> JSONResponse:
        if not resident_guid:
            return ddu_export_error_response(
                _RESIDENT_GUID_REQUIRED_RU,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rows = await self.repository.ddu_flat_list_by_resident(resident_guid)
            return ddu_export_success_response(rows)
        except DduExportDatabaseError as exc:
            return ddu_export_error_response(exc.message)
