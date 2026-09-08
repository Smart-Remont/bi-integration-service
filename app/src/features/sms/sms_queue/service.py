from typing import TYPE_CHECKING

from src.service import BaseService

from ..batching import iter_batches
from ..constants import SMS_BATCH_SIZE
from ..errors import SmsDatabaseError
from ..kcell_client import KcellClient, KcellClientError

if TYPE_CHECKING:
    from .repo import SmsQueueRepository


class SmsQueueService(BaseService):
    def __init__(self, repository: "SmsQueueRepository", kcell: KcellClient) -> None:
        self.repository = repository
        self.kcell = kcell

    async def process_queue(self) -> str:
        try:
            rows = await self.repository.sms_number_read()
            for batch_rows in iter_batches(rows, SMS_BATCH_SIZE):
                ids = [int(row["client_message_id"]) for row in batch_rows]
                _raw, result = await self.kcell.send_batches(
                    {"fail-fast": False, "messages": batch_rows},
                )
                await self.repository.sms_set_result(
                    ids,
                    str(result["batch_id"]),
                    str(result["created_at"]),
                )
            return "0"
        except (SmsDatabaseError, KcellClientError):
            raise
