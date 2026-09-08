from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import DDU_EXPORT_MODULE_CODE
from ..errors import to_ddu_export_database_error


class DduRoomListRepository(BaseRepository):
    async def ddu_room_list(self) -> SpRows:
        try:
            rows = await self.call_sp(
                "rest.ddu_room_list",
                cursor=True,
                module_code=DDU_EXPORT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_ddu_export_database_error(exc) from exc

        if not isinstance(rows, list):
            return []

        return rows
