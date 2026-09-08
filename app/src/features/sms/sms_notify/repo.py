import json

from src.repository import BaseRepository
from src.repository.base import SpRows

from ..constants import NOTIFY_MODULE_CODE
from ..errors import to_sms_database_error


class SmsNotifyRepository(BaseRepository):
    async def sms_notify__read(self) -> SpRows:
        try:
            return await self.call_sp(
                "notify.sms_notify__read",
                cursor=True,
                module_code=NOTIFY_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc

    async def sms_notify_result__set(
        self,
        ids: list[int],
        batch_id: str,
        created_at: str,
        response_raw: str,
        results: object | None,
    ) -> None:
        try:
            response_json = json.loads(response_raw)
            results_json = results if results is not None else None
            await self.call_sp(
                "notify.sms_notify_result__set",
                ids,
                batch_id,
                created_at,
                json.dumps(response_json),
                json.dumps(results_json) if results_json is not None else None,
                module_code=NOTIFY_MODULE_CODE,
            )
        except Exception as exc:
            raise to_sms_database_error(exc) from exc
