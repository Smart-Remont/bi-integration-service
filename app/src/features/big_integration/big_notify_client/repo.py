from src.repository import BaseRepository

from ..constants import DDU_MODULE_CODE
from ..db import scalar_from_sp_rows
from ..errors import BigIntegrationDatabaseError, to_big_integration_database_error


class BigNotifyClientRepository(BaseRepository):
    async def big_notify_client(self, raw_body: bytes) -> object:
        """Call ``rest.big_notify_client`` with the request body as a UTF-8 string."""
        body_text = raw_body.decode("utf-8") if raw_body else ""
        try:
            rows = await self.call_sp(
                "rest.big_notify_client",
                body_text,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        result = scalar_from_sp_rows(rows)
        if result is None:
            raise BigIntegrationDatabaseError(
                "Пустой ответ от rest.big_notify_client",
            )
        return result
