from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..json_helpers import parse_scalar_json
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import SrPresetListRepository


class SrPresetListService(BaseService):
    def __init__(self, repository: "SrPresetListRepository") -> None:
        self.repository = repository

    async def sr_preset_list(self, body: dict[str, object], host: str) -> JSONResponse:
        try:
            value = await self.repository.read_preset_for_big_app(body.get("city_id"), host)
            return legacy_bi_success_response(parse_scalar_json(value))
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
