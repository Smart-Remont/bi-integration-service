from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import (
    big_integration_notify_error_response,
    big_integration_notify_success_response,
)

if TYPE_CHECKING:
    from .repo import BigNotifyClientRepository

_METHOD_NOT_ALLOWED = "Неподдерживаемый метод"


class BigNotifyClientService(BaseService):
    def __init__(self, repository: "BigNotifyClientRepository") -> None:
        self.repository = repository

    async def big_notify_client(self, raw_body: bytes) -> JSONResponse:
        try:
            value = await self.repository.big_notify_client(raw_body)
            return big_integration_notify_success_response(value)
        except BigIntegrationDatabaseError as exc:
            return big_integration_notify_error_response(exc.message)

    def method_not_allowed(self) -> JSONResponse:
        return big_integration_notify_error_response(_METHOD_NOT_ALLOWED)
