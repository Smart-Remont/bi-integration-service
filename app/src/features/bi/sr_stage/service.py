from typing import TYPE_CHECKING, Any

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BiDatabaseError
from ..responses import bi_error_response, bi_success_response

if TYPE_CHECKING:
    from .repo import SrStageRepository


def _dedupe(events: list[Any]) -> list[dict[str, object]]:
    """Mirror legacy PHP dedup (``array_unique`` over serialized items)."""
    seen: set[tuple[object, object]] = set()
    result: list[dict[str, object]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        key = (event.get("iin"), event.get("id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


class SrStageService(BaseService):
    def __init__(self, repository: "SrStageRepository") -> None:
        self.repository = repository

    async def sr_stage(self, events: list[Any]) -> JSONResponse:
        results: list[dict[str, object]] = []
        try:
            for event in _dedupe(events):
                row = await self.repository.bi_sr_stage_v3(event.get("iin"), event.get("id"))
                if row:
                    results.append(row)
            return bi_success_response(results)
        except BiDatabaseError as exc:
            return bi_error_response(exc.message)
