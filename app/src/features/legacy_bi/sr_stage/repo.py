from src.repository import BaseRepository

from ..constants import LEGACY_BI_MODULE_CODE
from ..errors import to_legacy_bi_database_error


class SrStageRepository(BaseRepository):
    async def bi_sr_stage_v3(self, iin: object | None, flat_guid: object | None) -> dict[str, object] | None:
        try:
            rows = await self.call_sp(
                "rest.bi_sr_stage_v3",
                iin,
                flat_guid,
                cursor=True,
                module_code=LEGACY_BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_legacy_bi_database_error(exc) from exc

        return rows[0] if rows else None
