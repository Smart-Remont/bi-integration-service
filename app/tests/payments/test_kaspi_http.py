"""Unit tests: Kaspi HTTP routes (mocked service, no DB)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

from tests.payments.helpers import kaspi_result
from tests.payments.mock_deps import apply_payments_service_overrides, clear_payments_service_overrides


@pytest.fixture
async def payments_client() -> AsyncClient:
    apply_payments_service_overrides(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    clear_payments_service_overrides(app)


@pytest.mark.asyncio
async def test_kaspi_request_pay_returns_xml(payments_client: AsyncClient) -> None:
    response = await payments_client.get(
        "/api/payments/kaspi-request-pay",
        params={
            "command": "check",
            "txn_id": "HTTP-TX",
            "account": 1,
            "iin": "860515001730",
            "sum": 100,
        },
    )
    assert response.status_code == 200
    assert "text/xml" in response.headers.get("content-type", "")
    assert kaspi_result(response.text) == "0"


@pytest.mark.asyncio
async def test_kaspi_payment_pay_post_hidden_but_works(payments_client: AsyncClient) -> None:
    response = await payments_client.post(
        "/api/payments/kaspi-payment-pay",
        params={"command": "check", "txn_id": "HTTP-TX", "account": 1, "iin": "1", "sum": 1},
    )
    assert response.status_code == 200
    assert kaspi_result(response.text) == "0"
