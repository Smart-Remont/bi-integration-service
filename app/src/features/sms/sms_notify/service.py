from typing import TYPE_CHECKING, Any

from src.service import BaseService

from ..batching import iter_batches
from ..constants import SMS_BATCH_SIZE
from ..errors import SmsDatabaseError
from ..kcell_client import KcellClient, KcellClientError

if TYPE_CHECKING:
    from .repo import SmsNotifyRepository


def _results_value(parsed: dict[str, Any]) -> object | None:
    results = parsed.get("results")
    if results is None or results == []:
        return None
    return results


class SmsNotifyService(BaseService):
    def __init__(self, repository: "SmsNotifyRepository", kcell: KcellClient) -> None:
        self.repository = repository
        self.kcell = kcell

    async def process_notify_queue(self) -> str:
        try:
            rows = await self.repository.sms_notify__read()
            if not rows:
                return "No messages to send."

            for batch_rows in iter_batches(rows, SMS_BATCH_SIZE):
                ids = [int(row["client_message_id"]) for row in batch_rows]
                raw, parsed = await self.kcell.send_batches(
                    {"fail-fast": False, "messages": batch_rows},
                )
                await self.repository.sms_notify_result__set(
                    ids,
                    str(parsed["batch_id"]),
                    str(parsed["created_at"]),
                    raw,
                    _results_value(parsed),
                )
            return "0"
        except (SmsDatabaseError, KcellClientError):
            raise
