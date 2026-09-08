from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import CLIENT_MODULE_CODE
from ..errors import to_sms_database_error


class SmsQueueRepository(BaseRepository):
    async def sms_number_read(self) -> SpRows:
        try:
            return await self.call_sp(
                "client.sms_number_read",
                cursor=True,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc

    async def sms_set_result(
        self,
        ids: list[int],
        batch_id: str,
        created_at: str,
    ) -> None:
        try:
            await self.call_sp(
                "client.sms_set_result",
                ids,
                batch_id,
                created_at,
                module_code=CLIENT_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc
