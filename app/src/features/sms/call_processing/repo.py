import json

from src.repository import BaseRepository

from ..constants import SALE_MODULE_CODE
from ..errors import to_sms_database_error


class CallProcessingRepository(BaseRepository):
    async def client_call_hist_tab__insert(self, payload: dict[str, object]) -> None:
        try:
            await self.call_sp(
                "sale.client_call_hist_tab__insert",
                json.dumps(payload),
                module_code=SALE_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc
