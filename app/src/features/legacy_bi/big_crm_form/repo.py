from src.repository import BaseRepository

from ..constants import LEGACY_BI_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_legacy_bi_database_error


class BigCrmFormRepository(BaseRepository):
    async def request_from_bigcrm(self, body_json: str) -> object | None:
        try:
            rows = await self.call_sp(
                "crm.request_from_bigcrm",
                body_json,
                module_code=LEGACY_BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_legacy_bi_database_error(exc) from exc

        return scalar_from_sp_rows(rows)
