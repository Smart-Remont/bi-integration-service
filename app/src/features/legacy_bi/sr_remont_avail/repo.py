from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import LEGACY_BI_MODULE_CODE
from ..errors import to_legacy_bi_database_error


class SrRemontAvailRepository(BaseRepository):
    async def bi_cho_avail(self, block_guid_arr: list[str]) -> SpRows:
        try:
            return await self.call_sp(
                "rest.bi_cho_avail",
                block_guid_arr,
                cursor=True,
                module_code=LEGACY_BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_legacy_bi_database_error(exc) from exc
