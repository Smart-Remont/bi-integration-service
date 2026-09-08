from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..params import zero_to_null
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import DduFlatInfoRepository


class DduFlatInfoService(BaseService):
    def __init__(self, repository: "DduFlatInfoRepository") -> None:
        self.repository = repository

    async def ddu_flat_info(self, flat_guid: str) -> JSONResponse:
        try:
            row = await self.repository.ddu_flat_info(zero_to_null(flat_guid))
            return big_integration_success_response(row)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
