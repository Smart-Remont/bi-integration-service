"""Shared pytest fixtures for integrations-sr."""

from __future__ import annotations

import base64
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

_APP_DIR = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(os.path.join(_APP_DIR, ".env"), override=True)

# Unit-test defaults (only if .env did not set them).
os.environ.setdefault("INTEGRATION_HS_BI_USER", "hs_bi")
os.environ.setdefault("INTEGRATION_HS_BI_PASSWORD", "test-hs-bi-password")
os.environ.setdefault("DDU_EXPORT_AUTH_USER", "ddu_export")
os.environ.setdefault("DDU_EXPORT_AUTH_PASSWORD", "test-ddu-export-password")
os.environ.setdefault("OFFICE_PUBLIC_URL", "https://devprod.smart-remont.kz")

from src.main import app  # noqa: E402

from .ddu_integration.mock_deps import apply_ddu_get_service_overrides, clear_service_overrides  # noqa: E402


def _basic_auth_header(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def hs_bi_auth() -> dict[str, str]:
    return _basic_auth_header(
        os.environ["INTEGRATION_HS_BI_USER"],
        os.environ["INTEGRATION_HS_BI_PASSWORD"],
    )


@pytest.fixture
def ddu_export_auth() -> dict[str, str]:
    return _basic_auth_header(
        os.environ["DDU_EXPORT_AUTH_USER"],
        os.environ["DDU_EXPORT_AUTH_PASSWORD"],
    )


@pytest.fixture
def office_base_url() -> str:
    """Legacy PHP office host (devprod by default)."""
    return os.getenv("OFFICE_BASE_URL", "https://devprod.smart-remont.kz").rstrip("/")


@pytest.fixture
def integrations_base_url() -> str:
    """Running integrations-sr (local uvicorn or deployed)."""
    return os.getenv("INTEGRATIONS_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


@pytest.fixture
def live_credentials_configured() -> bool:
    hs_bi = (os.getenv("INTEGRATION_HS_BI_PASSWORD") or "").strip()
    ddu = (os.getenv("DDU_EXPORT_AUTH_PASSWORD") or "").strip()
    return bool(
        hs_bi
        and ddu
        and hs_bi != "test-hs-bi-password"
        and ddu != "test-ddu-export-password"
    )


@pytest.fixture
async def api_client() -> AsyncIterator[AsyncClient]:
    apply_ddu_get_service_overrides(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    clear_service_overrides(app)


@pytest.fixture
def assert_envelope() -> Any:
    def _assert(body: dict[str, Any], *, expect_success: bool = True) -> None:
        assert "data" in body
        assert "response" in body
        assert "error" in body
        assert body["response"] is expect_success
        if expect_success:
            assert isinstance(body["error"], dict)
            assert body["error"].get("message") == ""

    return _assert
