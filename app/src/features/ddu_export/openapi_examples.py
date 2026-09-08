"""OpenAPI response examples for Scalar / Swagger — DDU export endpoints."""

from typing import Any

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

DDU_EXPORT_LIST_RESPONSE: dict[int | str, dict[str, Any]] = {
    500: _ENVELOPE_ERR,
}

DDU_EXPORT_PARAM_RESPONSE: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Обязательный параметр не заполнен",
        "content": {
            "application/json": {
                "example": {
                    "data": None,
                    "response": False,
                    "error": {"message": "Параметр flat_guid обязателен"},
                },
            },
        },
    },
    500: _ENVELOPE_ERR,
}
