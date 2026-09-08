import json

from src.repository import BaseRepository
from src.repository.base import SpRows

from ..errors import to_big_integration_database_error

_DDU_MODULE_CODE = "DDU"


class RemontPresetListRepository(BaseRepository):
    async def ddu_preset_list(self, payload: dict[str, object]) -> SpRows:
        try:
            return await self.call_sp(
                "rest.ddu__preset_list",
                json.dumps(payload),
                cursor=True,
                module_code=_DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc
