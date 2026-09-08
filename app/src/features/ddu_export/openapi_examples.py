"""OpenAPI response examples for DDU Export (Scalar / Swagger)."""

from __future__ import annotations

from typing import Any

_EX_FLAT = "a0fef3a2-ea3e-4a83-820f-19a8dbb8c76c"
_EX_RESIDENT = "837a6dd5-8e5a-41f9-8eeb-006e1960a01c"
_EX_CLIENT_REQUEST_ID = 3218083

_ENVELOPE_ERR: dict[str, Any] = {
    "description": "Ошибка stored function",
    "content": {
        "application/json": {
            "example": {
                "data": None,
                "response": False,
                "error": {"message": "Параметр flat_guid обязателен"},
            },
        },
    },
}

_BAD_PARAM: dict[str, Any] = {
    "description": "Обязательный query-параметр не заполнен",
    "content": {
        "application/json": {
            "example": {
                "data": None,
                "response": False,
                "error": {"message": "Параметр flat_guid обязателен"},
            },
        },
    },
}


def ddu_export_responses(
    ok_data: Any,
    *,
    description: str = "Успешный ответ",
    include_400: bool = False,
) -> dict[int | str, dict[str, Any]]:
    out: dict[int | str, dict[str, Any]] = {
        200: {
            "description": description,
            "content": {
                "application/json": {
                    "example": {
                        "data": ok_data,
                        "response": True,
                        "error": {"message": ""},
                    },
                },
            },
        },
        500: _ENVELOPE_ERR,
    }
    if include_400:
        out[400] = _BAD_PARAM
    return out


DDU_EXPORT_LIST_RESPONSE = ddu_export_responses(
    [
        {
            "resident_guid": _EX_RESIDENT,
            "resident_name": "Тестовый житель",
            "iin": "781011400436",
        },
    ],
    description="Справочник жителей ДДУ",
)

DDU_EXPORT_ROOM_LIST_RESPONSE = ddu_export_responses(
    [{"room_id": 1, "room_name": "Спальня", "room_code": "BEDROOM"}],
    description="Справочник комнат",
)

DDU_EXPORT_ROOM_TYPE_LIST_RESPONSE = ddu_export_responses(
    [{"room_type_id": 1, "room_type_name": "Жилая"}],
    description="Справочник типов комнат",
)

DDU_EXPORT_PARAM_RESPONSE = ddu_export_responses(
    [
        {
            "flat_guid": _EX_FLAT,
            "flat_num": "101",
            "resident_guid": _EX_RESIDENT,
        },
    ],
    description="Список квартир жителя",
    include_400=True,
)

DDU_EXPORT_FLAT_REMONT_INFO_RESPONSE = ddu_export_responses(
    {
        "client_request_id": _EX_CLIENT_REQUEST_ID,
        "remont_id": 12345,
        "rooms": [
            {
                "room_id": 1,
                "room_name": "Спальня",
                "params": [
                    {
                        "object_param_id": 10,
                        "param_id": 5,
                        "param_name": "Площадь",
                        "param_code": "AREA",
                        "param_value": "12.5",
                    },
                ],
            },
        ],
    },
    description="Параметры ремонта, сгруппированные по комнатам",
    include_400=True,
)
