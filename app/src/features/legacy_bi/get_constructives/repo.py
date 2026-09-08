from src.repository import BaseRepository

from ..constants import LEGACY_BI_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import to_legacy_bi_database_error


class GetConstructivesRepository(BaseRepository):
    async def bi_get_client_request_material_json(self, client_request_id: object | None) -> object | None:
        try:
            rows = await self.call_sp(
                "rest.bi_get_client_request_material_json",
                client_request_id,
                module_code=LEGACY_BI_MODULE_CODE,
            )
        except Exception as exc:
            raise to_legacy_bi_database_error(exc) from exc

        return scalar_from_sp_rows(rows)
