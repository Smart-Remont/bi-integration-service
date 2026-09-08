from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import bi_error_response, bi_success_response

if TYPE_CHECKING:
    from .repo import GetConstructivesRepository


class GetConstructivesService(BaseService):
    def __init__(self, repository: "GetConstructivesRepository") -> None:
        self.repository = repository

    async def get_constructives(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.bi_get_client_request_material_json(body.get("application_id"))
            return bi_success_response(parse_scalar_json(value))
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
