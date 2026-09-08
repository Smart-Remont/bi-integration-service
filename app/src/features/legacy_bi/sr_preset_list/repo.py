from src.repository import BaseRepository

from ..constants import LEGACY_BI_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_legacy_bi_database_error


class SrPresetListRepository(BaseRepository):
    async def read_preset_for_big_app(self, city_id: object | None, host: str) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.read_preset_for_big_app",
                city_id,
                host,
                module_code=LEGACY_BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_legacy_bi_database_error(exc) from exc

        return scalar_from_sp_rows(rows)
