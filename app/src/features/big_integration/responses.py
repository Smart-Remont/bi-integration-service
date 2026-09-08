from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def big_integration_notify_success_response(data: Any) -> JSONResponse:
    """
    Response envelope for ``/big-notify-client``.

    Uses ``error.code`` (0 on success) and HTTP 400 on failure instead of 500.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": jsonable_encoder(data),
            "response": True,
            "error": {"code": 0, "message": ""},
        },
    )


def big_integration_notify_error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "data": {},
            "response": False,
            "error": {"code": 400, "message": message},
        },
    )


def big_integration_success_response(data: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "data": jsonable_encoder(data),
            "response": True,
            "error": {"message": ""},
        },
    )


def big_integration_error_response(
    message: str,
    *,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "data": None,
            "response": False,
            "error": {"message": message},
        },
    )
