from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import bi_error_response, bi_success_response

if TYPE_CHECKING:
    from .repo import SrRenderRepository


class SrRenderService(BaseService):
    def __init__(self, repository: "SrRenderRepository") -> None:
        self.repository = repository

    async def sr_render(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.bi_rakurs_list_v2(body.get("flat_guid"))
            return bi_success_response(parse_scalar_json(value))
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
