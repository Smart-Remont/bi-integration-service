"""Legacy BI/CRM response envelope.

Distinct from BIG Integration's envelope: on success ``error`` carries an
explicit ``code: 0``; on failure HTTP is **400** (not 500) and ``data`` carries
a ``P0xx`` error code (see ``errors.legacy_bi_error_code``) instead of ``null``.
Matches legacy PHP ``response_json()``.
"""

from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .errors import legacy_bi_error_code


def legacy_bi_success_response(data: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": jsonable_encoder(data),
            "response": True,
            "error": {"code": 0, "message": ""},
        },
    )


def legacy_bi_error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "data": legacy_bi_error_code(message),
            "response": False,
            "error": {"code": 400, "message": message},
        },
    )


def legacy_bi_method_not_allowed_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "data": None,
            "response": False,
            "error": {"code": 400, "message": "Неподдерживаемый метод"},
        },
    )
