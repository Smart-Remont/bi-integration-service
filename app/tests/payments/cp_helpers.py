"""Helpers for CloudPayments unit tests."""

from __future__ import annotations

from starlette.requests import Request


async def cp_request(
    body: bytes,
    *,
    content_type: str = "application/x-www-form-urlencoded",
) -> Request:
    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(b"content-type", content_type.encode())],
    }
    return Request(scope, receive)
