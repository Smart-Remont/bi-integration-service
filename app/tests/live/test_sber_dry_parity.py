"""Live parity: Sber dry-run — PHP devprod vs integrations-sr.

Run:
  uv run pytest app/tests/live/test_sber_dry_parity.py -m payments_parity -v
"""

from __future__ import annotations

import httpx
import pytest

from .payments_parity_helpers import SberParityCase, assert_sber_get_parity

pytestmark = [pytest.mark.live, pytest.mark.parity, pytest.mark.payments_parity]

SBER_DRY_CASES: tuple[SberParityCase, ...] = (
    SberParityCase(
        id="sber-callback-no-order",
        php_action="sberbank-callback",
        py_path="/api/payments/sberbank-callback",
    ),
    SberParityCase(
        id="sber-callback-unknown-order",
        php_action="sberbank-callback",
        py_path="/api/payments/sberbank-callback",
        params={"orderNumber": "999999999"},
    ),
    SberParityCase(
        id="sber-cron-empty",
        php_action="sberbank-check-payment-status",
        py_path="/api/payments/sberbank-check-payment-status",
    ),
)


@pytest.fixture
async def payments_parity_client(integrations_base_url: str) -> httpx.AsyncClient:
    timeout = httpx.Timeout(timeout=120.0, connect=15.0)
    client = httpx.AsyncClient(timeout=timeout)
    try:
        probe = await client.get(f"{integrations_base_url}/health")
        if probe.status_code != 200:
            pytest.skip(f"integrations-sr /health returned {probe.status_code}")
    except httpx.ConnectError:
        pytest.skip(f"integrations-sr not reachable at {integrations_base_url}")
    yield client
    await client.aclose()


@pytest.mark.parametrize("case", SBER_DRY_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_sber_dry_parity(
    case: SberParityCase,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    await assert_sber_get_parity(
        case=case,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
    )
