import json

from fastapi import Request
from fastapi.responses import JSONResponse

from .responses import big_integration_error_response


async def read_json_object(request: Request) -> dict[str, object] | JSONResponse:
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return big_integration_error_response("Invalid JSON")

    if not isinstance(body, dict):
        return big_integration_error_response("Invalid JSON")

    return body
