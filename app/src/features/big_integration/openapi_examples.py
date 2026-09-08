"""OpenAPI response examples for Scalar / Swagger."""

from typing import Any

_ENVELOPE_OK: dict[str, Any] = {
    "description": "Успешный ответ",
    "content": {
        "application/json": {
            "example": {
                "data": {"client_request_id": 2916069, "order_id": "318796"},
                "response": True,
                "error": {"message": ""},
            },
        },
    },
}

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

REQUEST_INFO_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: _ENVELOPE_OK,
    500: _ENVELOPE_ERR,
}

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

REQUEST_CONSTRUCTIVES_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Материалы и наполнение заявки",
        "content": {
            "application/json": {
                "example": {
                    "data": {
                        "placementUUID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "preset_id": 262,
                        "preset_name": "Стандарт",
                        "material_list": [],
                        "filling_list": [],
                    },
                    "response": True,
                    "error": {"message": ""},
                },
            },
        },
    },
    400: {
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
    },
    405: {
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
    },
    500: _ENVELOPE_ERR,
}
