from __future__ import annotations

from collections.abc import Awaitable
from typing import TypeVar

from fastapi.responses import PlainTextResponse

DatabaseErrorT = TypeVar("DatabaseErrorT", bound=Exception)


def get_error_message(exc: BaseException) -> str:
    message = getattr(exc, "message", None)
    if isinstance(message, str) and message:
        return message
    return str(exc)


async def plain_from(
    result: Awaitable[str],
    *,
    db_error: type[DatabaseErrorT],
    error_status_code: int = 500,
) -> PlainTextResponse:
    try:
        return PlainTextResponse(content=await result)
    except db_error as exc:
        return PlainTextResponse(content=get_error_message(exc), status_code=error_status_code)
