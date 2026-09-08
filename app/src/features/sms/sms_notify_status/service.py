from typing import TYPE_CHECKING, Any

from src.service import BaseService

from ..errors import SmsDatabaseError
from ..kcell_client import KcellClient, KcellClientError

if TYPE_CHECKING:
    from .repo import SmsNotifyStatusRepository


def _messages_value(parsed: dict[str, Any]) -> object | None:
    messages = parsed.get("messages")
    if messages is None or messages == []:
        return None
    return messages


class SmsNotifyStatusService(BaseService):
    def __init__(self, repository: "SmsNotifyStatusRepository", kcell: KcellClient) -> None:
        self.repository = repository
        self.kcell = kcell

    async def poll_batch_statuses(self) -> str:
        try:
            batches = await self.repository.sms_notify_batch__read()
            if not batches:
                return "No batches to check."

            for batch_row in batches:
                batch_id = str(batch_row["batch_id"])
                parsed = await self.kcell.check_batch_status(batch_id)
                messages = _messages_value(parsed)
                if messages is not None:
                    await self.repository.sms_notify_status__set(messages)

            return "0"
        except (SmsDatabaseError, KcellClientError):
            raise
