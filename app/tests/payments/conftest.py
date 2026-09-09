"""Fixtures for Payments unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.config import payments_config
from src.features.payments.kaspi.repo import KaspiRepository
from src.features.payments.kaspi.service import KaspiService


@pytest.fixture
def kaspi_allowed_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow any client IP (override default Kaspi allowlist)."""
    monkeypatch.setattr(payments_config, "kaspi_allowed_ips", ())


@pytest.fixture
def kaspi_repo_mock() -> AsyncMock:
    repo = AsyncMock(spec=KaspiRepository)
    repo.insert_kaspi_pay_log = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def kaspi_service(kaspi_repo_mock: AsyncMock) -> KaspiService:
    return KaspiService(kaspi_repo_mock)


@pytest.fixture
def sample_request_info() -> dict[str, str]:
    return {
        "prop_fio": "Иванов Иван",
        "prop_number": "14531",
        "prop_date": "2026-05-12",
        "resident_name": "4 Seasons",
        "company_name_official": "ТОО Smart Remont",
        "company_bin": "251240017509",
    }
