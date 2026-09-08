from typing import Any

from .repo import PresetRenderRepository

SectionRow = dict[str, Any]
PresetKitRow = dict[str, Any]
RoomRow = dict[str, Any]


class PresetResponseBuilder:
    def __init__(self, repository: PresetRenderRepository) -> None:
        self._repo = repository

    async def build_list_v2(
        self,
        placement_uuid: str,
        preset_kits: list[PresetKitRow],
        rooms: list[RoomRow],
    ) -> dict[str, object]:
        preset_list: list[dict[str, object]] = []
        for preset_kit in preset_kits:
            preset: dict[str, object] = dict(preset_kit)
            preset["features"] = await self._load_features(preset_kit["preset_id"])
            preset["additional"] = await self._load_additional_full(
                placement_uuid,
                preset_kit["preset_id"],
            )
            preset["renders"] = await self._load_renders(
                placement_uuid,
                preset_kit["preset_id"],
                rooms,
            )
            preset_list.append(preset)

        return {
            "placementUUID": placement_uuid,
            "preset_list": preset_list,
        }

    async def build_remont_preset(
        self,
        placement_uuid: str,
        preset_kits: list[PresetKitRow],
    ) -> dict[str, object]:
        preset_list: list[dict[str, object]] = []
        for preset_kit in preset_kits:
            preset: dict[str, object] = {
                "preset_id": preset_kit["preset_id"],
                "preset_name": preset_kit["preset_name"],
                "preset_price": preset_kit["preset_price"],
                "preset_guid": preset_kit["preset_guid"],
                "additional": await self._load_additional_compact(
                    placement_uuid,
                    preset_kit["preset_id"],
                ),
            }
            preset_list.append(preset)

        return {
            "placementUUID": placement_uuid,
            "preset_list": preset_list,
        }

    async def _load_features(self, preset_kit_id: object) -> list[dict[str, object]]:
        feature_groups = await self._repo.render_preset_feature_p_category_read(
            preset_kit_id,
        )
        features: list[dict[str, object]] = []
        for feature_group in feature_groups:
            group = dict(feature_group)
            group["items"] = await self._repo.render_preset_feature_read(
                preset_kit_id,
                group["feature_category_pid"],
            )
            features.append(group)
        return features

    async def _load_additional_full(
        self,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> list[dict[str, object]]:
        sections = await self._repo.render_filling_section_read(preset_kit_id)
        additional_list: list[dict[str, object]] = []

        for section in sections:
            code = section.get("section_show_type_code")
            if code == "CONSTRUCTOR_TAB_ROOM_WORK_SET":
                additional_list.append(
                    await self._section_room_work_set_full(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )
            elif code == "CONSTRUCTOR_TAB_WORK_SET":
                additional_list.append(
                    await self._section_work_set_full(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )
            elif code == "CONSTRUCTOR_TAB_ROOM":
                additional_list.append(
                    await self._section_room_full(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )
            elif code in ("CONSTRUCTOR_TAB", "FILLING"):
                additional_list.append(
                    await self._section_tab_filling_full(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )

        return additional_list

    async def _load_additional_compact(
        self,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> list[dict[str, object]]:
        sections = await self._repo.render_filling_section_read(preset_kit_id)
        additional_list: list[dict[str, object]] = []

        for section in sections:
            code = section.get("section_show_type_code")
            if code == "CONSTRUCTOR_TAB_ROOM_WORK_SET":
                additional_list.append(
                    await self._section_room_work_set_compact(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )
            elif code == "CONSTRUCTOR_TAB_WORK_SET":
                additional_list.append(
                    await self._section_work_set_compact(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )
            elif code == "CONSTRUCTOR_TAB_ROOM":
                additional_list.append(
                    await self._section_room_compact(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )
            elif code in ("CONSTRUCTOR_TAB", "FILLING"):
                additional_list.append(
                    await self._section_tab_filling_compact(
                        section,
                        placement_uuid,
                        preset_kit_id,
                    ),
                )

        return additional_list

    async def _load_renders(
        self,
        placement_uuid: str,
        preset_kit_id: object,
        rooms: list[RoomRow],
    ) -> dict[str, object]:
        renders: dict[str, object] = {
            "clean": {"rooms": []},
            "clean_with_filling": {"rooms": []},
        }
        clean_rooms: list[dict[str, object]] = []
        filling_rooms: list[dict[str, object]] = []

        for room in rooms:
            room_id = room.get("room_id")
            if room_id == -2:
                continue

            clean_views = await self._repo.render_read(
                placement_uuid,
                room_id,
                preset_kit_id,
                0,
            )
            filling_views = await self._repo.render_read(
                placement_uuid,
                room_id,
                preset_kit_id,
                1,
            )

            room_block = {
                "room_id": room_id,
                "room_name": room.get("room_name"),
                "room_name_kz": room.get("room_name_kz"),
                "room_code": room.get("room_code"),
            }
            clean_rooms.append({**room_block, "views": clean_views})
            filling_rooms.append({**room_block, "views": filling_views})

        renders["clean"] = {"rooms": clean_rooms}
        renders["clean_with_filling"] = {"rooms": filling_rooms}
        return renders

    async def _section_room_work_set_full(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["rooms"] = []
        rooms = await self._repo.render_filling_room_read(
            placement_uuid,
            preset_kit_id,
            section["section_id"],
        )
        for room in rooms:
            room_data = dict(room)
            room_data["work_sets"] = await self._work_sets_full(
                preset_kit_id,
                section["section_id"],
                room["room_id"],
                placement_uuid,
            )
            additional["rooms"].append(room_data)
        return additional

    async def _section_work_set_full(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["work_sets"] = await self._work_sets_full(
            preset_kit_id,
            section["section_id"],
            None,
            placement_uuid,
        )
        return additional

    async def _section_room_full(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["rooms"] = []
        rooms = await self._repo.render_filling_room_read(
            placement_uuid,
            preset_kit_id,
            section["section_id"],
        )
        for room in rooms:
            room_data = dict(room)
            room_data["work_sets"] = await self._work_sets_full(
                preset_kit_id,
                section["section_id"],
                room["room_id"],
                placement_uuid,
            )
            additional["rooms"].append(room_data)
        return additional

    async def _section_tab_filling_full(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["sets"] = await self._materials_full(
            preset_kit_id,
            section["section_id"],
            None,
            None,
            placement_uuid,
        )
        return additional

    async def _section_room_work_set_compact(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional: dict[str, object] = {
            "section_id": section["section_id"],
            "section_name": section["section_name"],
            "section_name_kz": section["section_name_kz"],
            "section_show_type_code": section["section_show_type_code"],
            "rooms": [],
        }
        rooms = await self._repo.render_filling_room_read(
            placement_uuid,
            preset_kit_id,
            section["section_id"],
        )
        for room in rooms:
            room_data = dict(room)
            room_data["work_sets"] = await self._work_sets_compact(
                preset_kit_id,
                section["section_id"],
                room["room_id"],
                placement_uuid,
            )
            additional["rooms"].append(room_data)
        return additional

    async def _section_work_set_compact(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["work_sets"] = await self._work_sets_compact(
            preset_kit_id,
            section["section_id"],
            None,
            placement_uuid,
        )
        return additional

    async def _section_room_compact(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["rooms"] = []
        rooms = await self._repo.render_filling_room_read(
            placement_uuid,
            preset_kit_id,
            section["section_id"],
        )
        for room in rooms:
            room_data = dict(room)
            room_data["work_sets"] = await self._work_sets_compact(
                preset_kit_id,
                section["section_id"],
                room["room_id"],
                placement_uuid,
            )
            additional["rooms"].append(room_data)
        return additional

    async def _section_tab_filling_compact(
        self,
        section: SectionRow,
        placement_uuid: str,
        preset_kit_id: object,
    ) -> dict[str, object]:
        additional = dict(section)
        additional["sets"] = await self._materials_compact(
            preset_kit_id,
            section["section_id"],
            None,
            None,
            placement_uuid,
        )
        return additional

    async def _work_sets_full(
        self,
        preset_kit_id: object,
        section_id: object,
        room_id: object | None,
        placement_uuid: str,
    ) -> list[dict[str, object]]:
        work_sets_out: list[dict[str, object]] = []
        work_sets = await self._repo.render_filling_work_set_read(
            preset_kit_id,
            section_id,
            room_id,
        )
        for work_set in work_sets:
            work_set_data = dict(work_set)
            work_set_data["sets"] = await self._materials_full(
                preset_kit_id,
                section_id,
                room_id,
                work_set["work_set_id"],
                placement_uuid,
            )
            work_sets_out.append(work_set_data)
        return work_sets_out

    async def _work_sets_compact(
        self,
        preset_kit_id: object,
        section_id: object,
        room_id: object | None,
        placement_uuid: str,
    ) -> list[dict[str, object]]:
        work_sets_out: list[dict[str, object]] = []
        work_sets = await self._repo.render_filling_work_set_read(
            preset_kit_id,
            section_id,
            room_id,
        )
        for work_set in work_sets:
            work_set_data = dict(work_set)
            work_set_data["sets"] = await self._materials_compact(
                preset_kit_id,
                section_id,
                room_id,
                work_set["work_set_id"],
                placement_uuid,
            )
            work_sets_out.append(work_set_data)
        return work_sets_out

    async def _materials_full(
        self,
        preset_kit_id: object,
        section_id: object,
        room_id: object | None,
        work_set_id: object | None,
        placement_uuid: str,
    ) -> list[dict[str, object]]:
        materials_out: list[dict[str, object]] = []
        materials = await self._repo.render_filling_material_set_read(
            preset_kit_id,
            section_id,
            room_id,
            work_set_id,
            placement_uuid,
        )
        for material in materials:
            materials_out.append(await self._material_full(material))
        return materials_out

    async def _materials_compact(
        self,
        preset_kit_id: object,
        section_id: object,
        room_id: object | None,
        work_set_id: object | None,
        placement_uuid: str,
    ) -> list[dict[str, object]]:
        sets_out: list[dict[str, object]] = []
        materials = await self._repo.render_filling_material_set_read(
            preset_kit_id,
            section_id,
            room_id,
            work_set_id,
            placement_uuid,
        )
        for material in materials:
            sets_out.append(_material_compact(material))
        return sets_out

    async def _material_full(self, material: dict[str, object]) -> dict[str, object]:
        material_data = dict(material)
        material_set_id = material_data.pop("material_set_id", None)
        preset_material_id = material_data["preset_material_id"]

        material_data["features"] = await self._repo.render_filling_features_read(
            preset_material_id,
        )
        material_data["items"] = await self._repo.render_filling_set_item_read(
            preset_material_id,
        )
        material_data["photos"] = await self._repo.render_set_photo_read(
            material_set_id,
        )
        return material_data


def _material_compact(material: dict[str, object]) -> dict[str, object]:
    material_data = dict(material)
    material_data.pop("material_set_id", None)
    return {
        "preset_material_id": material_data["preset_material_id"],
        "set_name": material_data["set_name"],
        "set_price": material_data["set_price"],
    }
