import httpx
from loguru import logger
from src.config import bi_config
from src.service import BaseService

from ..errors import BiDatabaseError
from .repo import ShowroomInfoListRepository


class ShowroomInfoListService(BaseService):
    def __init__(self, repository: ShowroomInfoListRepository) -> None:
        self.repository = repository

    async def proxy(self) -> tuple[str, int]:
        try:
            payload = await self.repository.read_marketing_remont_list()
        except BiDatabaseError as exc:
            logger.error("showroom-info-list DB error: {error}", error=exc.message)
            return exc.message, 500

        body = payload if isinstance(payload, str) else str(payload or "")
        timeout = httpx.Timeout(timeout=60.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    bi_config.showroom_info_url,
                    content=body,
                    headers={"Content-Type": "application/json"},
                )
        except httpx.RequestError as exc:
            logger.error("showroom-info-list upstream error: {error}", error=exc)
            return str(exc), 502

        return response.text, response.status_code
