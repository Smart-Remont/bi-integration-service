import json

from fastapi import Request
from fastapi.responses import JSONResponse

from .responses import bi_error_response

_INVALID_JSON_RU = "Неверный формат JSON"


async def read_json_object(request: Request) -> dict[str, object] | JSONResponse:
    """Parse a JSON object body; invalid input -> bi 400 envelope."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return bi_error_response(_INVALID_JSON_RU)

    if not isinstance(body, dict):
        return bi_error_response(_INVALID_JSON_RU)

    return body


async def read_json_array(request: Request) -> list[object] | JSONResponse:
    """Parse a JSON array body (used by ``/sr-stage``); invalid input -> 400."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return bi_error_response(_INVALID_JSON_RU)

    if not isinstance(body, list):
        return bi_error_response(_INVALID_JSON_RU)

    return body
