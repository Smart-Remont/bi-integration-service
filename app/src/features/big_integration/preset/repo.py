import json

from src.repository import BaseRepository
from src.repository.base import SpRow, SpRows

from ..constants import DDU_MODULE_CODE
from ..errors import to_big_integration_database_error


class PresetRenderRepository(BaseRepository):
    async def ddu_preset_list_v2(self, payload: dict[str, object]) -> SpRows:
        return await self._read_json_sp("rest.ddu__preset_list_v2", payload)

    async def render_plan_room_read(self, flat_guid: str) -> SpRows:
        return await self._read_sp("rest.render_plan_room__read", flat_guid)

    async def render_preset_feature_p_category_read(
        self,
        preset_kit_id: object,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_preset_feature_p_category__read",
            preset_kit_id,
        )

    async def render_preset_feature_read(
        self,
        preset_kit_id: object,
        pack_diff_category_id: object,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_preset_feature__read",
            preset_kit_id,
            pack_diff_category_id,
        )

    async def render_filling_section_read(self, preset_kit_id: object) -> SpRows:
        return await self._read_sp("rest.render_filling__section__read", preset_kit_id)

    async def render_filling_room_read(
        self,
        flat_guid: str,
        preset_kit_id: object,
        section_id: object,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_filling__room_read",
            flat_guid,
            preset_kit_id,
            section_id,
        )

    async def render_filling_work_set_read(
        self,
        preset_kit_id: object,
        section_id: object,
        room_id: object | None,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_filling__work_set_read",
            preset_kit_id,
            section_id,
            room_id,
        )

    async def render_filling_material_set_read(
        self,
        preset_kit_id: object,
        section_id: object,
        room_id: object | None,
        work_set_id: object | None,
        flat_guid: str | None,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_filling__material_set_read",
            preset_kit_id,
            section_id,
            room_id,
            work_set_id,
            flat_guid,
        )

    async def render_filling_features_read(
        self,
        preset_material_id: object,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_filling_features__read",
            preset_material_id,
        )

    async def render_filling_set_item_read(
        self,
        preset_material_id: object,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render_filling__set_item_read",
            preset_material_id,
        )

    async def render_set_photo_read(self, material_set_id: object) -> SpRows:
        return await self._read_sp("rest.render_set_photo__read", material_set_id)

    async def render_read(
        self,
        flat_guid: str,
        room_id: object,
        preset_kit_id: object,
        is_mebel: int,
    ) -> SpRows:
        return await self._read_sp(
            "rest.render__read",
            flat_guid,
            room_id,
            preset_kit_id,
            is_mebel,
        )

    async def _read_json_sp(self, sp_name: str, payload: dict[str, object]) -> SpRows:
        try:
            rows = await self.call_sp(
                sp_name,
                json.dumps(payload),
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not isinstance(rows, list):
            return []

        return rows

    async def _read_sp(self, sp_name: str, *args: object) -> SpRows:
        try:
            rows = await self.call_sp(
                sp_name,
                *args,
                cursor=True,
                module_code=DDU_MODULE_CODE,
            )
        except Exception as exc:
            raise to_big_integration_database_error(exc) from exc

        if not isinstance(rows, list):
            return []

        return rows
