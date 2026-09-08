from src.repository import BaseRepository

from .constants import PUBLIC_MODULE_CODE
from .db import scalar_from_sp_rows
from .errors import to_signing_database_error


class SigningSettingsRepository(BaseRepository):
    async def get_setting_value_by_code(self, setting_code: str) -> str | None:
        try:
            rows = await self.call_sp(
                "public.get_setting_value_by_code",
                setting_code,
                module_code=PUBLIC_MODULE_CODE,
            )
        except Exception as exc:
            raise to_signing_database_error(exc) from exc

        value = scalar_from_sp_rows(rows)
        if value is None:
            return None
        return str(value)
