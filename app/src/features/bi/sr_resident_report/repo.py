from src.repository import BaseRepository

from ..constants import BI_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_bi_database_error


class SrResidentReportRepository(BaseRepository):
    async def sr_resident_report(self) -> object | None:
        try:
            rows = await self.call_sp("rest.sr_resident_report", module_code=BI_MODULE_CODE)
        except Exception as exc:
            raise to_bi_database_error(exc) from exc

        return scalar_from_sp_rows(rows)
