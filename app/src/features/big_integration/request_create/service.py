from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import RequestCreateRepository


class RequestCreateService(BaseService):
    """Legacy v1 proxy: same envelope/flow as ``request-create-v3``, older SP."""

    def __init__(self, repository: "RequestCreateRepository") -> None:
        self.repository = repository

    async def request_create(self, body: dict[str, object]) -> JSONResponse:
        try:
            client_request_id = await self.repository.ddu_create_request(body)
            row = await self.repository.ddu_request_get(client_request_id)
            return big_integration_success_response(row)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
