import json

from src.repository import BaseRepository
from src.repository.base import SpRows

from ..errors import BigIntegrationDatabaseError, to_big_integration_database_error

_DDU_MODULE_CODE = "DDU"


class DduFlatInfoMultipleRepository(BaseRepository):
    async def ddu_flat_info_multiple(self, flat_guids: list[str]) -> SpRows:
        payload = {"flat_guids": flat_guids}
        try:
            rows = await self.call_sp(
                "rest.ddu_flat_info_multiple",
                json.dumps(payload),
                cursor=True,
                module_code=_DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not isinstance(rows, list):
            raise BigIntegrationDatabaseError(
                "Некорректный ответ от rest.ddu_flat_info_multiple",
            )

        return rows
