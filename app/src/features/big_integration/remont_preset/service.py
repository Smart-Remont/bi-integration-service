from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from src.service import BaseService

from ..errors import BigIntegrationDatabaseError
from ..responses import big_integration_error_response, big_integration_success_response

if TYPE_CHECKING:
    from ..preset.builder import PresetResponseBuilder
    from ..preset.repo import PresetRenderRepository


class RemontPresetService(BaseService):
    def __init__(
        self,
        repository: "PresetRenderRepository",
        builder: "PresetResponseBuilder",
    ) -> None:
        self._repository = repository
        self._builder = builder

    async def remont_preset(self, body: dict[str, object]) -> JSONResponse:
        placement_uuid = str(body["placementUUID"])
        try:
            preset_kits = await self._repository.ddu_preset_list_v2(body)
            response_data = await self._builder.build_remont_preset(
                placement_uuid,
                preset_kits,
            )
            return big_integration_success_response(response_data)
        except BigIntegrationDatabaseError as exc:
            return big_integration_error_response(exc.message)
