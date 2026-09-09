"""OpenAPI request/response examples for BIG Integration (Scalar / Swagger)."""

from __future__ import annotations

from typing import Any

from src.openapi_helpers import json_request_body

# GUID с непустым preset_list на devprod (parity).
_EX_PLACEMENT = "c0f17482-ca65-4e58-8446-d1b155f45945"
_EX_PRESET_ID = 428
_EX_CLIENT_REQUEST_ID = 3218083

_ENVELOPE_ERR: dict[str, Any] = {
    "description": "Ошибка stored function",
    "content": {
        "application/json": {
            "example": {
                "data": None,
                "response": False,
                "error": {"message": "Поле \"client_request_id\" не заполнено [ДДУ]"},
            },
        },
    },
}

_BAD_JSON: dict[str, Any] = {
    "description": "Невалидный JSON",
    "content": {
        "application/json": {
            "example": {
                "data": None,
                "response": False,
                "error": {"message": "Неверный формат JSON"},
            },
        },
    },
}

_METHOD_NOT_ALLOWED: dict[str, Any] = {
    "description": "Допускается только POST",
    "content": {
        "application/json": {
            "example": {
                "data": None,
                "response": False,
                "error": {"message": "Неподдерживаемый метод"},
            },
        },
    },
}


def _envelope_ok(data: Any, *, description: str = "Успешный ответ") -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "example": {
                    "data": data,
                    "response": True,
                    "error": {"message": ""},
                },
            },
        },
    }


def standard_post_responses(
    *,
    ok_data: Any,
    ok_description: str = "Успешный ответ",
    include_405: bool = False,
) -> dict[int | str, dict[str, Any]]:
    out: dict[int | str, dict[str, Any]] = {
        200: _envelope_ok(ok_data, description=ok_description),
        400: _BAD_JSON,
        500: _ENVELOPE_ERR,
    }
    if include_405:
        out[405] = _METHOD_NOT_ALLOWED
    return out


REQUEST_INFO_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: _envelope_ok(
        {"client_request_id": _EX_CLIENT_REQUEST_ID, "order_id": "343835"},
        description="Данные заявки / квартиры",
    ),
    500: _ENVELOPE_ERR,
}

REQUEST_CREATE_V3_BODY = json_request_body(
    {
        "application_id": None,
        "order_id": "ORD-123",
        "deal_id": None,
        "placementUUID": _EX_PLACEMENT,
        "preset_id": _EX_PRESET_ID,
        "full_name": "Иванов Иван Иванович",
        "phone_number": "+77001234567",
        "email": "client@example.com",
        "birth_date": "01.01.1990",
        "iin": "900101300123",
        "status": "NEW",
        "request_type": "FULL_REMONT",
        "request_price": 1500000,
        "selected_sets": [
            {"preset_material_id": 12345, "set_name": "Комплект мебели"},
        ],
    },
)

REQUEST_CREATE_V3_RESPONSE = standard_post_responses(
    ok_data={
        "client_request_id": _EX_CLIENT_REQUEST_ID,
        "application_id": None,
        "order_id": "ORD-123",
        "deal_id": None,
    },
    ok_description="Заявка создана или найдена (идемпотентность по ИИН)",
)

REQUEST_EVENT_V3_BODY = json_request_body(
    {
        "client_request_id": _EX_CLIENT_REQUEST_ID,
        "placementUUID": _EX_PLACEMENT,
        "order_id": "343835",
        "status": "DEAL_CREATED",
        "request_type": "FULL_REMONT",
    },
)

REQUEST_EVENT_V3_RESPONSE = REQUEST_CREATE_V3_RESPONSE

REPAIR_PACK_PRICES_BODY = json_request_body(
    {"placementUUIDs": [_EX_PLACEMENT]},
)

REPAIR_PACK_PRICES_RESPONSE = standard_post_responses(
    ok_data=[
        {
            "placementUUID": _EX_PLACEMENT,
            "preset_guid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "preset_name": "BIG+ Basic 2.0",
            "preset_price": "1500000",
            "optimal_price": "1800000",
            "optimal_preset_guid": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
            "optimal_preset_name": "BIG+ Optimal",
            "is_old_repair_package": False,
            "status": True,
            "error": None,
        },
    ],
    ok_description="Цены пакетов по каждому GUID",
)

DDU_FLAT_INFO_MULTIPLE_BODY = json_request_body(
    {"flat_guids": [_EX_PLACEMENT]},
)

DDU_FLAT_INFO_MULTIPLE_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: _envelope_ok(
        [
            {
                "flat_guid": _EX_PLACEMENT,
                "client_request_id": _EX_CLIENT_REQUEST_ID,
                "status_code": "ACTIVE",
            },
        ],
        description="Строки заявок (может быть несколько на одну квартиру)",
    ),
    400: {
        "description": "Пустой или неверный flat_guids",
        "content": {
            "application/json": {
                "example": {
                    "data": None,
                    "response": False,
                    "error": {"message": "Массив flat_guids не может быть пустым"},
                },
            },
        },
    },
    500: _ENVELOPE_ERR,
}

DDU_RESIDENT_AGREEMENT_BODY = json_request_body(
    {
        "resident_guid": "837a6dd5-8e5a-41f9-8eeb-006e1960a01c",
        "agreement_status": "SIGNED",
        "event_date": "2026-09-08 12:00:00",
    },
)

DDU_RESIDENT_AGREEMENT_RESPONSE = standard_post_responses(
    ok_data=None,
    ok_description="Запись в лог; data=null при успехе",
)

REMONT_PRESET_LIST_V2_BODY = json_request_body({"placementUUID": _EX_PLACEMENT})

REMONT_PRESET_LIST_V2_RESPONSE = standard_post_responses(
    ok_data={
        "placementUUID": _EX_PLACEMENT,
        "preset_list": [
            {
                "preset_id": _EX_PRESET_ID,
                "preset_name": "BIG+ Basic 2.0",
                "preset_price": "1500000",
                "features": [],
                "additional": [],
                "renders": {"clean": [], "clean_with_filling": []},
            },
        ],
    },
    ok_description="Каталог пресетов с features, additional, renders",
    include_405=True,
)

REMONT_PRESET_BODY = json_request_body(
    {"placementUUID": _EX_PLACEMENT, "preset_id": _EX_PRESET_ID},
)

REMONT_PRESET_RESPONSE = standard_post_responses(
    ok_data={
        "placementUUID": _EX_PLACEMENT,
        "preset_list": [
            {
                "preset_id": _EX_PRESET_ID,
                "preset_name": "BIG+ Basic 2.0",
                "preset_price": "1500000",
                "preset_guid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "additional": [],
            },
        ],
    },
    ok_description="Один пресет, компактное наполнение",
    include_405=True,
)

REMONT_PRESET_LIST_V1_BODY = REMONT_PRESET_LIST_V2_BODY

REMONT_PRESET_LIST_V1_RESPONSE = standard_post_responses(
    ok_data={
        "placementUUID": _EX_PLACEMENT,
        "preset_list": [{"preset_id": _EX_PRESET_ID, "preset_name": "BIG+ Basic 2.0"}],
    },
    ok_description="Legacy v1: `ddu__preset_list`",
)

REQUEST_CONSTRUCTIVES_BODY = json_request_body(
    {"client_request_id": _EX_CLIENT_REQUEST_ID},
)

REQUEST_CONSTRUCTIVES_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Материалы и наполнение заявки",
        "content": {
            "application/json": {
                "example": {
                    "data": {
                        "placementUUID": _EX_PLACEMENT,
                        "preset_id": _EX_PRESET_ID,
                        "preset_name": "BIG+ Basic 2.0",
                        "material_list": [],
                        "filling_list": [],
                    },
                    "response": True,
                    "error": {"message": ""},
                },
            },
        },
    },
    400: _BAD_JSON,
    405: _METHOD_NOT_ALLOWED,
    500: _ENVELOPE_ERR,
}

BIG_NOTIFY_CLIENT_BODY = json_request_body(
    {
        "client_request_id": _EX_CLIENT_REQUEST_ID,
        "notify_type": "STATUS_CHANGE",
        "message": "Текст уведомления",
    },
)

BIG_NOTIFY_CLIENT_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Уведомление принято",
        "content": {
            "application/json": {
                "example": {
                    "data": 12345,
                    "response": True,
                    "error": {"code": 0, "message": ""},
                },
            },
        },
    },
    400: {
        "description": "Ошибка обработки или неверный HTTP-метод",
        "content": {
            "application/json": {
                "example": {
                    "data": {},
                    "response": False,
                    "error": {"code": 400, "message": "Неподдерживаемый метод"},
                },
            },
        },
    },
}
