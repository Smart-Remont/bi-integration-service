import json

from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import NOTIFY_MODULE_CODE
from ..errors import to_sms_database_error


class SmsNotifyStatusRepository(BaseRepository):
    async def sms_notify_batch__read(self) -> SpRows:
        try:
            return await self.call_sp(
                "notify.sms_notify_batch__read",
                cursor=True,
                module_code=NOTIFY_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc

    async def sms_notify_status__set(self, messages: object) -> None:
        try:
            await self.call_sp(
                "notify.sms_notify_status__set",
                json.dumps(messages),
                module_code=NOTIFY_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc
