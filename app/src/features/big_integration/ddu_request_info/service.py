from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..params import zero_to_null
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import DduRequestInfoRepository


class DduRequestInfoService(BaseService):
    def __init__(self, repository: "DduRequestInfoRepository") -> None:
        self.repository = repository

    async def ddu_request_info(self, client_request_id: int) -> JSONResponse:
        try:
            row = await self.repository.ddu_request_info_by_client_request(
                zero_to_null(client_request_id),
            )
            return big_integration_success_response(row)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
