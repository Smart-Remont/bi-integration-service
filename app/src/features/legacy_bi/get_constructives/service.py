from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import GetConstructivesRepository


class GetConstructivesService(BaseService):
    def __init__(self, repository: "GetConstructivesRepository") -> None:
        self.repository = repository

    async def get_constructives(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.bi_get_client_request_material_json(body.get("application_id"))
            return legacy_bi_success_response(parse_scalar_json(value))
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
