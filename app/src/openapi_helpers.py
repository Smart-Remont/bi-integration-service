"""Shared OpenAPI / Scalar / Swagger text and route helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

_CRON_HTTP_NOTE = (
    "\n\n**HTTP (Scalar/Swagger):** в схеме указан **GET**; **POST** принимается тем же handler "
    "(скрыт из OpenAPI). Логика идентична legacy PHP — метод не проверялся. Crontab: достаточно GET."
)

_PLAIN_CRON_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Cron завершён (в т.ч. пустая очередь)",
        "content": {"text/plain": {"schema": {"type": "string", "example": "0"}}},
    },
    500: {"description": "Ошибка БД или внешнего сервиса"},
}


def legacy_integration_path(action: str) -> str:
    """Zend route: IntegrationController → /integration/{action}."""
    return f"\n\n**Legacy PHP:** `/integration/{action}` (`IntegrationController.php`)."


def legacy_client_path(action: str) -> str:
    """Zend route: ClientController → /client/{action}."""
    return f"\n\n**Legacy PHP:** `/client/{action}` (`ClientController.php`)."


def cron_description(body: str, *, php_action: str | None = None) -> str:
    text = body
    if php_action:
        text += legacy_integration_path(php_action)
    return text + _CRON_HTTP_NOTE


def integration_controller_description(body: str, *, url_action: str, php_method: str) -> str:
    """OpenAPI text for hs_bi IntegrationController POST endpoints."""
    return (
        f"{body}\n\n"
        f"**PHP:** `IntegrationController::{php_method}` → `/integration/{url_action}`.\n"
        f"**Auth:** Basic `hs_bi` (`INTEGRATION_HS_BI_*`). Конверт `response_json()` — HTTP 400, `P0xx`."
    )


def add_cron_route(
    router: APIRouter,
    path: str,
    *,
    summary: str,
    description: str,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register GET (visible in OpenAPI) + POST (hidden), same handler."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        router.get(
            path,
            summary=summary,
            description=description,
            response_class=PlainTextResponse,
            responses=_PLAIN_CRON_RESPONSES,
            **kwargs,
        )(func)
        router.post(path, include_in_schema=False)(func)
        return func

    return decorator
