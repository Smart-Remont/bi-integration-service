from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import SrRequestListRepository


class SrRequestListService(BaseService):
    def __init__(self, repository: "SrRequestListRepository") -> None:
        self.repository = repository

    async def sr_request_list(self, body: dict[str, object]) -> JSONResponse:
        try:
            rows = await self.repository.bi_client_request_list(
                body.get("iin"),
                body.get("flat_guid"),
                body.get("discount_percent"),
            )
            return legacy_bi_success_response(rows)
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
