"""Live parity: Kaspi check (read-only) — PHP devprod vs integrations-sr.

Both services must use the same PostgreSQL (dev_prod_smartremont).

Required in app/.env (skip case if missing):
  TEST_KASPI_CLIENT_REQUEST_ID, TEST_KASPI_IIN, TEST_KASPI_SUM
  TEST_KASPI_CLIENT_REQUEST_PAYMENT_ID, TEST_KASPI_PAYMENT_IIN, TEST_KASPI_PAYMENT_SUM

Run:
  uv run pytest app/tests/live/test_kaspi_check_parity.py -m payments_parity -v

integrations-sr must be up at INTEGRATIONS_BASE_URL (default http://127.0.0.1:8000).
Office: OFFICE_BASE_URL (default https://devprod.smart-remont.kz).
"""

from __future__ import annotations

import httpx
import pytest

from .payments_parity_helpers import (
    KaspiParityCase,
    assert_kaspi_get_parity,
    kaspi_env_snapshot,
    resolve_kaspi_params,
)

pytestmark = [pytest.mark.live, pytest.mark.parity, pytest.mark.payments_parity]

KASPI_CHECK_CASES: tuple[KaspiParityCase, ...] = (
    KaspiParityCase(
        id="kaspi-request-check-ok",
        php_action="kaspi-request-pay",
        py_path="/api/payments/kaspi-request-pay",
        params={
            "command": "check",
            "account": 0,
            "iin": "",
            "sum": 0,
            "txn_id": "",
        },
        required_env=(
            ("account", "TEST_KASPI_CLIENT_REQUEST_ID"),
            ("iin", "TEST_KASPI_IIN"),
            ("sum", "TEST_KASPI_SUM"),
        ),
        generate_txn_id=True,
    ),
    KaspiParityCase(
        id="kaspi-request-check-wrong-iin",
        php_action="kaspi-request-pay",
        py_path="/api/payments/kaspi-request-pay",
        params={
            "command": "check",
            "account": 0,
            "iin": "000000000000",
            "sum": 0,
            "txn_id": "",
        },
        required_env=(
            ("account", "TEST_KASPI_CLIENT_REQUEST_ID"),
            ("sum", "TEST_KASPI_SUM"),
        ),
        generate_txn_id=True,
    ),
    KaspiParityCase(
        id="kaspi-request-check-missing-txn",
        php_action="kaspi-request-pay",
        py_path="/api/payments/kaspi-request-pay",
        params={
            "command": "check",
            "account": 0,
            "iin": "",
            "sum": 0,
        },
        required_env=(
            ("account", "TEST_KASPI_CLIENT_REQUEST_ID"),
            ("iin", "TEST_KASPI_IIN"),
            ("sum", "TEST_KASPI_SUM"),
        ),
    ),
    KaspiParityCase(
        id="kaspi-payment-check-ok",
        php_action="kaspi-payment-pay",
        py_path="/api/payments/kaspi-payment-pay",
        params={
            "command": "check",
            "account": 0,
            "iin": "",
            "sum": 0,
            "txn_id": "",
        },
        required_env=(
            ("account", "TEST_KASPI_CLIENT_REQUEST_PAYMENT_ID"),
            ("iin", "TEST_KASPI_PAYMENT_IIN"),
            ("sum", "TEST_KASPI_PAYMENT_SUM"),
        ),
        generate_txn_id=True,
    ),
    KaspiParityCase(
        id="kaspi-payment-check-not-found",
        php_action="kaspi-payment-pay",
        py_path="/api/payments/kaspi-payment-pay",
        params={
            "command": "check",
            "account": 999999999,
            "iin": "000000000000",
            "sum": 1,
            "txn_id": "PARITY-KASPI-NOT-FOUND",
        },
    ),
    KaspiParityCase(
        id="kaspi-unknown-command",
        php_action="kaspi-request-pay",
        py_path="/api/payments/kaspi-request-pay",
        params={
            "command": "foo",
            "txn_id": "PARITY-KASPI-UNKNOWN",
        },
    ),
)


@pytest.fixture
async def payments_parity_client(integrations_base_url: str) -> httpx.AsyncClient:
    timeout = httpx.Timeout(timeout=60.0, connect=15.0)
    client = httpx.AsyncClient(timeout=timeout)
    try:
        probe = await client.get(f"{integrations_base_url}/health")
        if probe.status_code != 200:
            pytest.skip(f"integrations-sr /health returned {probe.status_code}")
    except httpx.ConnectError:
        pytest.skip(f"integrations-sr not reachable at {integrations_base_url}")
    yield client
    await client.aclose()


@pytest.mark.parametrize("case", KASPI_CHECK_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_kaspi_check_parity(
    case: KaspiParityCase,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    env = kaspi_env_snapshot()
    if case.id == "kaspi-payment-check-ok":
        payment_iin = (env.get("TEST_KASPI_PAYMENT_IIN") or env.get("TEST_KASPI_IIN") or "").strip()
        if payment_iin:
            env = {**env, "TEST_KASPI_PAYMENT_IIN": payment_iin}

    params = resolve_kaspi_params(case, env=env)
    if params is None:
        missing = [env_name for _, env_name in case.required_env]
        pytest.skip(f"Set env for case {case.id}: {missing}")

    await assert_kaspi_get_parity(
        case=case,
        params=params,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
    )
