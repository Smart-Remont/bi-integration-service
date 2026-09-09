"""Unit tests: CloudPayments HTTP route (mocked service)."""

from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

from tests.payments.mock_deps import (
    apply_cloud_payments_service_overrides,
    clear_payments_service_overrides,
)


@pytest.fixture
async def cp_client() -> AsyncClient:
    apply_cloud_payments_service_overrides(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    clear_payments_service_overrides(app)


@pytest.mark.asyncio
async def test_cloudpayments_check_post_returns_json(cp_client: AsyncClient) -> None:
    response = await cp_client.post(
        "/api/payments/cloudpayments/mode/check",
        content="InvoiceId=inv&Data=%7B%22hash%22%3A%22stub%22%7D",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert response.json() == {"code": 0}
