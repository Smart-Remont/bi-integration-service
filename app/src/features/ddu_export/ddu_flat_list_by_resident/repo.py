from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import DDU_EXPORT_MODULE_CODE
from ..errors import to_ddu_export_database_error


class DduFlatListByResidentRepository(BaseRepository):
    async def ddu_flat_list_by_resident(self, resident_guid: str) -> SpRows:
        try:
            rows = await self.call_sp(
                "rest.ddu_flat_list_by_resident",
                resident_guid,
                cursor=True,
                module_code=DDU_EXPORT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_ddu_export_database_error(exc) from exc

        if not isinstance(rows, list):
            return []

        return rows
