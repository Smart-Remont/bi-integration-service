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
            raw_id = body.get("application_id")
            client_request_id = int(raw_id) if raw_id not in (None, "") else None
            value = await self.repository.bi_get_client_request_material_json(client_request_id)
            return bi_success_response(parse_scalar_json(value))
        except (BiDatabaseError, ValueError, TypeError) as exc:
            return bi_error_response(str(exc) if not isinstance(exc, BiDatabaseError) else exc.message)
