from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import RequestEventRepository


class RequestEventService(BaseService):
    """Legacy v1: same as ``request-event-v3``, older SP, drops ``client_request_id``."""

    def __init__(self, repository: "RequestEventRepository") -> None:
        self.repository = repository

    async def request_event(self, body: dict[str, object]) -> JSONResponse:
        try:
            client_request_id = await self.repository.ddu_request_event(body)
            row = await self.repository.ddu_request_get(client_request_id)
            response_data = dict(row) if row else None
            if response_data is not None:
                response_data.pop("client_request_id", None)
            return big_integration_success_response(response_data)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
