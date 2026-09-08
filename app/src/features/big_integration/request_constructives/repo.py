import json

from src.repository import BaseRepository
from src.repository.base import SpRow, SpRows

from ..constants import DDU_MODULE_CODE
from ..errors import to_big_integration_database_error


class RequestConstructivesRepository(BaseRepository):
    async def ddu_client_material__read(self, payload: dict[str, object]) -> SpRows:
        return await self._read_json_sp(
            "rest.ddu_client_material__read",
            payload,
        )

    async def ddu_client_filling__read(self, payload: dict[str, object]) -> SpRows:
        return await self._read_json_sp(
            "rest.ddu_client_filling__read",
            payload,
        )

    async def ddu_request_full_info(self, payload: dict[str, object]) -> SpRow | None:
        try:
            rows = await self.call_sp(
                "rest.ddu_request_full_info",
                json.dumps(payload),
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not rows:
            return None

        return rows[0]

    async def _read_json_sp(
        self,
        sp_name: str,
        payload: dict[str, object],
    ) -> SpRows:
        try:
            rows = await self.call_sp(
                sp_name,
                json.dumps(payload),
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not isinstance(rows, list):
            return []

        return rows
