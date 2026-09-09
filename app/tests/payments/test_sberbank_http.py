"""Unit tests: Sber HTTP routes (mocked services)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

from tests.payments.mock_deps import (
    apply_sber_service_overrides,
    clear_payments_service_overrides,
)


@pytest.fixture
async def sber_client() -> AsyncClient:
    apply_sber_service_overrides(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    clear_payments_service_overrides(app)


@pytest.mark.asyncio
async def test_sberbank_callback_get_returns_plain_zero(sber_client: AsyncClient) -> None:
    response = await sber_client.get("/api/payments/sberbank-callback")
    assert response.status_code == 200
    assert response.text == "0"


@pytest.mark.asyncio
async def test_sberbank_cron_get_returns_plain_zero(sber_client: AsyncClient) -> None:
    response = await sber_client.get("/api/payments/sberbank-check-payment-status")
    assert response.status_code == 200
    assert response.text == "0"
