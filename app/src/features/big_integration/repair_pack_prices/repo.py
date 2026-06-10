from src.repository import BaseRepository
from src.repository.base import SpRow

from ..errors import to_big_integration_database_error

_DDU_MODULE_CODE = "DDU"


class RepairPackPricesRepository(BaseRepository):
    async def ddu_repair_pack_info_get(self, placement_uuid: str) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "rest.ddu_repair_pack_info__get",
                placement_uuid,
                cursor=True,
                module_code=_DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not rows:
            return None

        return rows[0]
