from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..params import zero_to_null
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import RequestInfoRepository


class RequestInfoService(BaseService):
    def __init__(self, repository: "RequestInfoRepository") -> None:
        self.repository = repository

    async def request_info(
        self,
        deal_id: str,
        application_id: str,
        order_id: str,
    ) -> JSONResponse:
        try:
            row = await self.repository.ddu_request_info(
                zero_to_null(deal_id),
                zero_to_null(application_id),
                zero_to_null(order_id),
            )
            return big_integration_success_response(row)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
