"""OpenAPI response examples for Scalar / Swagger — legacy BI/CRM endpoints."""

from typing import Any

LEGACY_BI_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Успешный ответ",
        "content": {
            "application/json": {
                "example": {
                    "data": {},
                    "response": True,
                    "error": {"code": 0, "message": ""},
                },
            },
        },
    },
    400: {
        "description": "Ошибка stored function или неверный HTTP-метод",
        "content": {
            "application/json": {
                "example": {
                    "data": "P001",
                    "response": False,
                    "error": {"code": 400, "message": "P001 Планировка не найдена"},
                },
            },
        },
    },
}
