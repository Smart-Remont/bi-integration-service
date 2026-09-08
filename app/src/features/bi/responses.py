"""IntegrationController (hs_bi) response envelope.

Distinct from BIG Integration's envelope: on success ``error`` carries an
explicit ``code: 0``; on failure HTTP is **400** (not 500) and ``data`` carries
a ``P0xx`` error code (see ``errors.bi_error_code``) instead of ``null``.
Matches legacy PHP ``response_json()``.
"""

from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse

from src.php_json import php_jsonable_encoder

from .errors import bi_error_code


def bi_success_response(data: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": php_jsonable_encoder(data),
            "response": True,
            "error": {"code": 0, "message": ""},
        },
    )


def bi_error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "data": bi_error_code(message),
            "response": False,
            "error": {"code": 400, "message": message},
        },
    )


def bi_method_not_allowed_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "data": None,
            "response": False,
            "error": {"code": 400, "message": "Неподдерживаемый метод"},
        },
    )
