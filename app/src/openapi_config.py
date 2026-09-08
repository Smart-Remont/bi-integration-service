"""Custom OpenAPI schema for Scalar / Swagger (servers, metadata)."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def configure_openapi(app: FastAPI) -> None:
    """Attach custom OpenAPI with server URLs for Try-it in Scalar."""

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )

        servers: list[dict[str, str]] = [
            {
                "url": "http://127.0.0.1:8000",
                "description": "Local (uvicorn)",
            },
        ]
        public_base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
        if public_base and public_base not in {s["url"] for s in servers}:
            servers.append(
                {
                    "url": public_base,
                    "description": "Deployed (PUBLIC_BASE_URL)",
                },
            )
        office = (os.getenv("OFFICE_PUBLIC_URL") or "").strip().rstrip("/")
        if office:
            servers.append(
                {
                    "url": office,
                    "description": "Legacy PHP office (reference only)",
                },
            )

        schema["servers"] = servers
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
