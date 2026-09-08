from src.repository import BaseRepository

from ..constants import LEGACY_BI_MODULE_CODE
from ..errors import to_legacy_bi_database_error


class RemontAvailRepository(BaseRepository):
    async def bi_remont_avail(
        self,
        flat_guid: object | None,
        resident_guid: object | None,
        flat_num: object | None,
    ) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.bi_remont_avail",
                flat_guid,
                resident_guid,
                flat_num,
                cursor=True,
                module_code=LEGACY_BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_legacy_bi_database_error(exc) from exc

        if not rows:
            return None
        return next(iter(rows[0].values()))
