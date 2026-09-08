import json
from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import RequestConstructivesRepository


class RequestConstructivesService(BaseService):
    def __init__(self, repository: "RequestConstructivesRepository") -> None:
        self.repository = repository

    async def request_constructives(self, body: dict[str, object]) -> JSONResponse:
        try:
            material_list = await self.repository.ddu_client_material__read(body)
            filling_list = await self.repository.ddu_client_filling__read(body)
            filling_list = _decode_characteristic_json(filling_list)

            request_info = await self.repository.ddu_request_full_info(body) or {}

            response_data: dict[str, object] = {
                "placementUUID": request_info.get("flat_guid"),
                "preset_id": request_info.get("preset_kit_id"),
                "preset_name": request_info.get("preset_kit_name"),
                "material_list": material_list,
                "filling_list": filling_list,
            }
            return big_integration_success_response(response_data)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)


def _decode_characteristic_json(
    filling_list: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Parse string ``characteristic_json`` fields into JSON objects."""
    decoded: list[dict[str, object]] = []
    for filling in filling_list:
        item = dict(filling)
        characteristic = item.get("characteristic_json")
        if isinstance(characteristic, str):
            try:
                item["characteristic_json"] = json.loads(characteristic)
            except json.JSONDecodeError:
                pass
        decoded.append(item)
    return decoded
