from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import ChangeRequestStatusRepository


class ChangeRequestStatusService(BaseService):
    def __init__(self, repository: "ChangeRequestStatusRepository") -> None:
        self.repository = repository

    async def change_request_status(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.bi_change_request_status(
                body.get("application_id"),
                body.get("status_code"),
            )
            return legacy_bi_success_response(value)
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
