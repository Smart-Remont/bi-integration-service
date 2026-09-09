"""OpenAPI examples for MyNCA signing callbacks (Scalar / Swagger)."""

from __future__ import annotations

from typing import Any

from src.openapi_helpers import json_request_body

_ACK_OK = {"status": True}
_ACK_ERR = {"status": False, "error": "sign_process_id не указан"}
_ACK_BAD_JSON = {"status": False, "error": "Невалидный JSON в callback"}

MYNCA_CALLBACK_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Callback принят (в т.ч. non-SUCCESS для client-sign — ack без записи)",
        "content": {"application/json": {"example": _ACK_OK}},
    },
    400: {
        "description": "Тело не JSON-объект",
        "content": {"application/json": {"example": _ACK_BAD_JSON}},
    },
    500: {
        "description": "Ошибка валидации / SP (MyNCA должен ретраить)",
        "content": {"application/json": {"example": _ACK_ERR}},
    },
}

CLIENT_SIGN_BODY = json_request_body(
    {
        "sign_process_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "SUCCESS",
        "ext_id": 3210140,
        "dn_name": "CN=IVANOV IVAN,SERIALNUMBER=IIN123456789012",
        "group_id": "g-1",
        "meta_data": {
            "type_code": "CLIENT_SIGN",
            "doc_type": "AGREEMENT",
            "client_request_id": 3210140,
            "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        },
    }
)

PROJECT_REMONT_BODY = json_request_body(
    {
        "sign_process_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "SUCCESS",
        "is_signed": True,
        "ext_id": 77808,
        "dn_name": "CN=IVANOV IVAN,SERIALNUMBER=IIN123456789012",
    }
)

CABINET_ACT_BODY = json_request_body(
    {
        "sign_process_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "group_id": "g-1",
        "status": "SUCCESS",
        "is_signed": True,
        "ext_id": 12345,
        "dn_name": "CN=IVANOV IVAN,SERIALNUMBER=IIN123456789012",
        "signer": {"subject": {"dn": "CN=IVANOV IVAN,SERIALNUMBER=IIN123456789012"}},
    }
)

THIRD_PARTY_FORM_BODY: dict[str, Any] = {
    "requestBody": {
        "required": True,
        "content": {
            "application/x-www-form-urlencoded": {
                "schema": {
                    "type": "object",
                    "required": ["id", "dn_name", "signed_xml", "sign_process_id"],
                    "properties": {
                        "id": {"type": "string", "description": "client_request_credit_detail_id"},
                        "dn_name": {"type": "string"},
                        "signed_xml": {"type": "string", "description": "base64 XML с PDF в узле str"},
                        "sign_process_id": {"type": "string"},
                    },
                },
                "example": {
                    "id": "17961",
                    "dn_name": "CN=IVANOV,SERIALNUMBER=IIN123456789012",
                    "signed_xml": "PE...base64...",
                    "sign_process_id": "proc-1",
                },
            }
        },
    }
}

THIRD_PARTY_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Подпись принята",
        "content": {
            "text/plain": {
                "example": '{"status": true, "value": null, "error": null}',
            }
        },
    },
    400: {
        "description": "Недостаточно параметров / XML",
        "content": {
            "text/plain": {
                "example": '{"status": false, "value": null, "error": "Недостаточно параметров"}',
            }
        },
    },
    500: {
        "description": "Ошибка БД",
        "content": {
            "text/plain": {
                "example": '{"status": false, "value": null, "error": "..."}',
            }
        },
    },
}
