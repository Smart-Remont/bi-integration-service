from src.repository import BaseRepository
from src.repository.base import SpRow

from ..constants import DDU_MODULE_CODE
from ..errors import to_big_integration_database_error


class DduFlatInfoRepository(BaseRepository):
    async def ddu_flat_info(self, flat_guid: object | None) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "rest.ddu_flat_info",
                flat_guid,
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not rows:
            return None

        return rows[0]
