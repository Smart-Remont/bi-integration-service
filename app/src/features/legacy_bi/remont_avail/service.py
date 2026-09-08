from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import RemontAvailRepository


class RemontAvailService(BaseService):
    def __init__(self, repository: "RemontAvailRepository") -> None:
        self.repository = repository

    async def remont_avail(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.bi_remont_avail(
                body.get("flat_guid"),
                body.get("resident_guid"),
                body.get("flat_num"),
            )
            return legacy_bi_success_response(value)
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
