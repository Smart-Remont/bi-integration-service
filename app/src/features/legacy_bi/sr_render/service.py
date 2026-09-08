from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import SrRenderRepository


class SrRenderService(BaseService):
    def __init__(self, repository: "SrRenderRepository") -> None:
        self.repository = repository

    async def sr_render(self, body: dict[str, object]) -> JSONResponse:
        try:
            value = await self.repository.bi_rakurs_list_v2(body.get("flat_guid"))
            return legacy_bi_success_response(parse_scalar_json(value))
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
