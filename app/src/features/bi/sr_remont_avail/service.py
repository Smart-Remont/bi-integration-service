from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..responses import bi_error_response, bi_success_response

if TYPE_CHECKING:
    from .repo import SrRemontAvailRepository


def _block_guid_arr(body: dict[str, object]) -> list[str]:
    raw = body.get("realEstateUUIDs")
    if not isinstance(raw, list):
        return []
    return _unique_preserve_order([str(item) for item in raw])


def _unique_preserve_order(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


class SrRemontAvailService(BaseService):
    def __init__(self, repository: "SrRemontAvailRepository") -> None:
        self.repository = repository

    async def sr_remont_avail(self, body: dict[str, object]) -> JSONResponse:
        try:
            rows = await self.repository.bi_cho_avail(_block_guid_arr(body))
            return bi_success_response({"avail_list": rows})
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
