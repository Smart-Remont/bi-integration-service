from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import RequestCreateV2Repository


class RequestCreateV2Service(BaseService):
    """
    Same SP as ``request-create-v3`` (``ddu__create_request_v2``), legacy v2
    envelope drops ``client_request_id`` from the response (PHP ``unset()``).
    """

    def __init__(self, repository: "RequestCreateV2Repository") -> None:
        self.repository = repository

    async def request_create_v2(self, body: dict[str, object]) -> JSONResponse:
        try:
            client_request_id = await self.repository.ddu_create_request_v2(body)
            row = await self.repository.ddu_request_get(client_request_id)
            response_data = dict(row) if row else None
            if response_data is not None:
                response_data.pop("client_request_id", None)
            return big_integration_success_response(response_data)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
