from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import DduExportDatabaseError
from ..responses import ddu_export_error_response, ddu_export_success_response

if TYPE_CHECKING:
    from .repo import DduRoomListRepository


class DduRoomListService(BaseService):
    def __init__(self, repository: "DduRoomListRepository") -> None:
        self.repository = repository

    async def ddu_room_list(self) -> JSONResponse:
        try:
            rows = await self.repository.ddu_room_list()
            return ddu_export_success_response(rows)
        except DduExportDatabaseError as exc:
            return ddu_export_error_response(exc.message)
