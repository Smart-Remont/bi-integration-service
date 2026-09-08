from typing import TYPE_CHECKING

from fastapi import status
from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from .repo import RemontPresetListRepository

_EMPTY_GUID_RU = "ГУИД помещения не может быть пустым"


class RemontPresetListService(BaseService):
    """Legacy v1: SP `ddu__preset_list` (older than `remont-preset-list-v2`'s `ddu__preset_list_v2`)."""

    def __init__(self, repository: "RemontPresetListRepository") -> None:
        self.repository = repository

    async def remont_preset_list(self, body: dict[str, object]) -> JSONResponse:
        placement_uuid = body.get("placementUUID")
        if not isinstance(placement_uuid, str) or not placement_uuid.strip():
            return big_integration_error_response(
                _EMPTY_GUID_RU,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            preset_list = await self.repository.ddu_preset_list(body)
            return big_integration_success_response(
                {"placementUUID": placement_uuid, "preset_list": preset_list},
            )
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
