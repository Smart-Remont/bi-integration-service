from typing import TYPE_CHECKING

from fastapi import status
from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import DduExportDatabaseError
from ..responses import ddu_export_error_response, ddu_export_success_response
from .room_nesting import nest_flat_remont_info_by_room

if TYPE_CHECKING:
    from .repo import DduFlatRemontInfoRepository

_FLAT_GUID_REQUIRED_RU = 'Параметр flat_guid обязателен'


class DduFlatRemontInfoService(BaseService):
    def __init__(self, repository: "DduFlatRemontInfoRepository") -> None:
        self.repository = repository

    async def ddu_flat_remont_info(self, flat_guid: str) -> JSONResponse:
        if not flat_guid:
            return ddu_export_error_response(
                _FLAT_GUID_REQUIRED_RU,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rows = await self.repository.ddu_flat_remont_info(flat_guid)
            return ddu_export_success_response(nest_flat_remont_info_by_room(rows))
        except DduExportDatabaseError as exc:
            return ddu_export_error_response(exc.message)
