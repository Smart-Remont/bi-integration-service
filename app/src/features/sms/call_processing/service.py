from typing import TYPE_CHECKING

from src.service import BaseService

from ..errors import SmsDatabaseError

if TYPE_CHECKING:
    from .repo import CallProcessingRepository


class CallProcessingService(BaseService):
    def __init__(self, repository: "CallProcessingRepository") -> None:
        self.repository = repository

    async def insert_call_webhook(self, payload: dict[str, object]) -> dict[str, object]:
        try:
            await self.repository.client_call_hist_tab__insert(payload)
            return {"status": True}
        except SmsDatabaseError as exc:
            return {"status": False, "error": exc.message}
