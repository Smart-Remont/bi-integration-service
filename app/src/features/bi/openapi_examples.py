"""OpenAPI request/response examples for IntegrationController (hs_bi)."""

from __future__ import annotations

from typing import Any

from src.openapi_helpers import json_request_body

_EX_FLAT = "a0fef3a2-ea3e-4a83-820f-19a8dbb8c76c"
_EX_FLAT_PRESETS = "c0f17482-ca65-4e58-8446-d1b155f45945"
_EX_RESIDENT = "837a6dd5-8e5a-41f9-8eeb-006e1960a01c"
_EX_REAL_ESTATE = "4139ed34-817e-4e05-9397-a2dc08162ab8"
_EX_IIN = "781011400436"
_EX_APPLICATION_ID = 59942

_BI_ERR_400: dict[str, Any] = {
    "description": "Ошибка SP или валидации",
    "content": {
        "application/json": {
            "example": {
                "data": "P400",
                "response": False,
                "error": {"code": 400, "message": "Неверный код статуса"},
            },
        },
    },
}

_BI_ERR_JSON: dict[str, Any] = {
    "description": "Невалидный JSON",
    "content": {
        "application/json": {
            "example": {
                "data": "P400",
                "response": False,
                "error": {"code": 400, "message": "Неверный формат JSON"},
            },
        },
    },
}


def bi_responses(ok_data: Any, *, description: str = "Успешный ответ") -> dict[int | str, dict[str, Any]]:
    return {
        200: {
            "description": description,
            "content": {
                "application/json": {
                    "example": {
                        "data": ok_data,
                        "response": True,
                        "error": {"code": 0, "message": ""},
                    },
                },
            },
        },
        400: _BI_ERR_400,
    }


LEGACY_BI_RESPONSE = bi_responses({}, description="Успешный ответ (структура data зависит от SP)")

EMPTY_BODY = json_request_body({})

SR_RENDER_BODY = json_request_body({"flat_guid": _EX_FLAT})
SR_RENDER_RESPONSE = bi_responses(
    {"rakurs_list": [{"rakurs_id": 1, "rakurs_name": "Гостиная"}]},
    description="JSON из `bi_rakurs_list_v2` (parse_scalar_json)",
)

SR_REQUEST_LIST_BODY = json_request_body(
    {"flat_guid": _EX_FLAT, "iin": _EX_IIN, "discount_percent": 0},
)
SR_REQUEST_LIST_RESPONSE = bi_responses(
    [{"client_request_id": 3218083, "status_code": "ACTIVE"}],
    description="Список заявок по квартире",
)

SR_PRESET_LIST_BODY = json_request_body({"city_id": 1})
SR_PRESET_LIST_RESPONSE = bi_responses(
    {"presets": [{"preset_id": 428, "preset_name": "BIG+ Basic 2.0"}]},
    description="Каталог пресетов для BI-приложения",
)

SR_RENDER_AVAIL_BODY = json_request_body({"flat_guid": [_EX_FLAT_PRESETS]})
SR_RENDER_AVAIL_RESPONSE = bi_responses(
    {"avail_list": [{"flat_guid": _EX_FLAT_PRESETS, "avail": True}]},
    description="Наличие рендера по GUID",
)

SR_REMONT_AVAIL_BODY = json_request_body({"realEstateUUIDs": [_EX_REAL_ESTATE]})
SR_REMONT_AVAIL_RESPONSE = bi_responses(
    {"avail_list": [{"real_estate_guid": _EX_REAL_ESTATE, "avail": True}]},
    description="Наличие ремонта по ЖК",
)

SR_STAGE_BODY = json_request_body([{"iin": _EX_IIN, "id": _EX_FLAT}])
SR_STAGE_RESPONSE = bi_responses(
    [{"iin": _EX_IIN, "id": _EX_FLAT, "stage_name": "Черновая отделка"}],
    description="Этап ремонта по каждому элементу массива",
)

SR_SHOWROOM_REPORT_RESPONSE = bi_responses(
    [{"showroom_id": 1, "showroom_name": "Showroom A"}],
    description="Отчёт шоурумов (JSON-строка из SP)",
)

SR_RESIDENT_REPORT_RESPONSE = bi_responses(
    [{"resident_guid": _EX_RESIDENT, "flat_count": 3}],
    description="Отчёт жителей (JSON-строка из SP)",
)

REMONT_AVAIL_BODY = json_request_body({"flat_guid": _EX_FLAT})
REMONT_AVAIL_RESPONSE = bi_responses(
    {"avail": True, "flat_guid": _EX_FLAT},
    description="Первая строка SP `bi_remont_avail`",
)

GET_CONSTRUCTIVES_BODY = json_request_body({"application_id": _EX_APPLICATION_ID})
GET_CONSTRUCTIVES_RESPONSE = bi_responses(
    {"materials": [], "fillings": []},
    description="JSON из `bi_get_client_request_material_json`",
)

CHANGE_REQUEST_STATUS_BODY = json_request_body(
    {"application_id": _EX_APPLICATION_ID, "status_code": "CLIENT_INFO"},
)
CHANGE_REQUEST_STATUS_RESPONSE = bi_responses(
    {"application_id": _EX_APPLICATION_ID, "status_code": "CLIENT_INFO"},
    description="Статус заявки обновлён",
)

BIGAPP_FORM_BODY = json_request_body(
    {
        "fio": "Иванов Иван Иванович",
        "phone": "+77001234567",
        "city_id": 1,
        "comment": "Заявка из BI-приложения",
    },
)
BIGAPP_FORM_RESPONSE = bi_responses(
    {"lead_id": 1001},
    description="Лид создан в CRM",
)

BIG_CRM_FORM_BODY = json_request_body(
    {
        "fio": "Петров Пётр Петрович",
        "phone": "+77007654321",
        "source": "big_crm",
    },
)
BIG_CRM_FORM_RESPONSE = BIGAPP_FORM_RESPONSE

CRM_CREATE_REQUEST_BODY = json_request_body(
    {"flat_guid": _EX_FLAT, "iin": _EX_IIN, "phone": "+77001234567"},
)
CRM_CREATE_CLIENT_REQUEST_EMPTY_BODY = json_request_body({"flat_guid": _EX_FLAT})
CRM_CREATE_CLIENT_REQUEST_AGREEMENT_BODY = json_request_body(
    {"flat_guid": _EX_FLAT, "iin": _EX_IIN, "application_id": _EX_APPLICATION_ID},
)
CRM_LEGACY_RESPONSE = bi_responses(
    {"client_request_id": 3218083},
    description="Ответ SP (если доступен на окружении)",
)
SR_REMONT_REPORT_RESPONSE = bi_responses(
    [{"flat_guid": _EX_FLAT, "remont_status": "ACTIVE"}],
    description="Отчёт ремонтов (JSON-строка из SP)",
)

SHOWROOM_INFO_LIST_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Ответ BI Opera (JSON или plain text)",
        "content": {
            "application/json": {
                "example": [{"id": 1, "name": "Showroom"}],
            },
            "text/plain": {
                "example": "OK",
            },
        },
    },
    502: {"description": "Ошибка прокси или BI Opera"},
}
