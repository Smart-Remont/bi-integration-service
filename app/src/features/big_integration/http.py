import json

from fastapi import Request, status
from fastapi.responses import JSONResponse

from .responses import big_integration_error_response

_INVALID_JSON_RU = "Неверный формат JSON"


async def read_json_object(request: Request) -> dict[str, object] | JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return big_integration_error_response(
            "Invalid JSON",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(body, dict):
        return big_integration_error_response(
            "Invalid JSON",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return body


async def read_json_object_ru(
    request: Request,
) -> dict[str, object] | JSONResponse:
    """Parse JSON body; invalid input → 400 with message «Неверный формат JSON»."""
    raw = await request.body()
    if not raw:
        return big_integration_error_response(
            _INVALID_JSON_RU,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return big_integration_error_response(
            _INVALID_JSON_RU,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(body, dict):
        return big_integration_error_response(
            _INVALID_JSON_RU,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return body


async def read_raw_body(request: Request) -> bytes:
    """Return request body bytes unchanged (for SP that accept raw JSON text)."""
    return await request.body()
