from src.service import BaseService

from ..shared_repo import PaymentsRepository
from ..sberbank_client import SberbankClient


class SberbankCheckStatusService(BaseService):
    def __init__(self, repository: PaymentsRepository, sber: SberbankClient) -> None:
        self.repository = repository
        self.sber = sber

    async def poll(self) -> str:
        pending = await self.repository.sberbank_payment_read_for_status()
        for item in pending:
            result = await self.sber.get_order_status_extended(
                item.get("cp_transaction_id"),
                item.get("client_request_payment_id"),
            )
            if result.get("actionCode") == 0:
                attributes = result.get("attributes") or []
                transaction_id = attributes[0].get("value") if attributes else None
                await self.repository.sberbank_client_request_payment_set(
                    result.get("orderNumber"),
                    item["client_request_id"],
                    transaction_id,
                    PaymentsRepository.bank_info_json(result.get("bankInfo")),
                )
        return "0"
