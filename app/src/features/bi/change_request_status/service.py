from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..responses import bi_error_response, bi_success_response

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
            return bi_success_response(value)
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
