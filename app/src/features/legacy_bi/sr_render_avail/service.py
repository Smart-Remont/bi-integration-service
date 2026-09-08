from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import LegacyBiDatabaseError
from ..responses import legacy_bi_error_response, legacy_bi_success_response

if TYPE_CHECKING:
    from .repo import SrRenderAvailRepository


def _flat_guid_arr(body: dict[str, object]) -> list[str]:
    raw = body.get("flat_guid")
    if not isinstance(raw, list):
        return []
    return sorted({str(item) for item in raw})


class SrRenderAvailService(BaseService):
    def __init__(self, repository: "SrRenderAvailRepository") -> None:
        self.repository = repository

    async def sr_render_avail(self, body: dict[str, object]) -> JSONResponse:
        try:
            rows = await self.repository.bi_render_avail(_flat_guid_arr(body))
            return legacy_bi_success_response({"avail_list": rows})
        except LegacyBiDatabaseError as exc:
            return legacy_bi_error_response(exc.message)
