"""Mutating parity: Payments write flows — PHP devprod vs integrations-sr.

Requires PAYMENTS_MUTATING=1 in app/.env and dedicated test fixtures (not prod clients).

Kaspi pay uses separate PHP/PY fixtures per side — the same txn_id cannot be paid twice
(PHP then FastAPI with one txn_id yields result=3 on the second caller).

Run:
  PAYMENTS_MUTATING=1 uv run pytest app/tests/live/test_payments_mutating_parity.py -v
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import httpx
import pytest

from .payments_parity_helpers import (
    SberParityCase,
    assert_cp_mutating_post_parity,
    assert_kaspi_pay_mutating_parity,
    assert_sber_get_parity,
    kaspi_mutating_env_snapshot,
)

pytestmark = [
    pytest.mark.live,
    pytest.mark.parity,
    pytest.mark.payments_parity,
    pytest.mark.mutating,
]


def _require_env(*names: str) -> dict[str, str] | None:
    env = kaspi_mutating_env_snapshot()
    out: dict[str, str] = {}
    for name in names:
        raw = (env.get(name) or "").strip()
        if not raw:
            return None
        out[name] = raw
    return out


def _kaspi_txn_id(prefix: str) -> str:
    configured = (os.getenv("TEST_KASPI_MUTATING_TXN_ID_PREFIX") or "PARITY-KASPI").strip()
    return f"{configured}-{prefix}-{uuid.uuid4().hex[:10]}"


def _txn_date() -> str:
    """SP kaspi_request_pay expects YYYYMMDDHH24MISS (same as legacy PHP)."""
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


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


@pytest.mark.asyncio
async def test_cloudpayments_fail_mutating_parity(
    payments_mutating_enabled: None,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    env = _require_env(
        "TEST_CP_MUTATING_REQUEST_HASH",
        "TEST_CP_MUTATING_INVOICE_HASH",
        "TEST_CP_MUTATING_AMOUNT",
    )
    if env is None:
        pytest.skip("Set TEST_CP_MUTATING_* in app/.env")

    body = (
        f"InvoiceId={env['TEST_CP_MUTATING_INVOICE_HASH']}"
        f"&Data=%7B%22hash%22%3A%22{env['TEST_CP_MUTATING_REQUEST_HASH']}%22%7D"
        f"&Amount={env['TEST_CP_MUTATING_AMOUNT']}"
        "&TransactionId=tx-cp-fail"
    )

    await assert_cp_mutating_post_parity(
        case_id="cp-fail-mutating",
        mode="fail",
        body=body,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
        expect_code=0,
    )


@pytest.mark.asyncio
async def test_sber_callback_deposited_status_zero_mutating(
    payments_mutating_enabled: None,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    """deposited + status≠1 → sberbank_transaction_set, no Sber HTTP API."""
    env = _require_env("TEST_SBER_MUTATING_ORDER_NUMBER")
    if env is None:
        pytest.skip("Set TEST_SBER_MUTATING_ORDER_NUMBER in app/.env")

    case = SberParityCase(
        id="sber-callback-deposited-status-zero",
        php_action="sberbank-callback",
        py_path="/api/payments/sberbank-callback",
        params={
            "orderNumber": env["TEST_SBER_MUTATING_ORDER_NUMBER"],
            "operation": "deposited",
            "status": "0",
            "mdOrder": "parity-md-order",
        },
    )
    await assert_sber_get_parity(
        case=case,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
    )


@pytest.mark.asyncio
async def test_kaspi_request_pay_mutating_parity(
    payments_mutating_enabled: None,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    env = _require_env(
        "TEST_KASPI_MUTATING_PHP_CLIENT_REQUEST_ID",
        "TEST_KASPI_MUTATING_PHP_IIN",
        "TEST_KASPI_MUTATING_PHP_SUM",
        "TEST_KASPI_MUTATING_PY_CLIENT_REQUEST_ID",
        "TEST_KASPI_MUTATING_PY_IIN",
        "TEST_KASPI_MUTATING_PY_SUM",
    )
    if env is None:
        pytest.skip("Set TEST_KASPI_MUTATING_PHP_* and TEST_KASPI_MUTATING_PY_* in app/.env")

    php_params = {
        "command": "pay",
        "account": int(env["TEST_KASPI_MUTATING_PHP_CLIENT_REQUEST_ID"]),
        "iin": env["TEST_KASPI_MUTATING_PHP_IIN"],
        "sum": int(env["TEST_KASPI_MUTATING_PHP_SUM"]),
        "txn_id": _kaspi_txn_id("req-pay-php"),
        "txn_date": _txn_date(),
    }
    py_params = {
        "command": "pay",
        "account": int(env["TEST_KASPI_MUTATING_PY_CLIENT_REQUEST_ID"]),
        "iin": env["TEST_KASPI_MUTATING_PY_IIN"],
        "sum": int(env["TEST_KASPI_MUTATING_PY_SUM"]),
        "txn_id": _kaspi_txn_id("req-pay-py"),
        "txn_date": _txn_date(),
    }

    await assert_kaspi_pay_mutating_parity(
        case_id="kaspi-request-pay-mutating",
        php_action="kaspi-request-pay",
        py_path="/api/payments/kaspi-request-pay",
        php_params=php_params,
        py_params=py_params,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
    )


@pytest.mark.asyncio
async def test_kaspi_payment_pay_mutating_parity(
    payments_mutating_enabled: None,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    env = _require_env(
        "TEST_KASPI_MUTATING_PHP_PAYMENT_ID",
        "TEST_KASPI_MUTATING_PHP_PAYMENT_IIN",
        "TEST_KASPI_MUTATING_PHP_PAYMENT_SUM",
        "TEST_KASPI_MUTATING_PY_PAYMENT_ID",
        "TEST_KASPI_MUTATING_PY_PAYMENT_IIN",
        "TEST_KASPI_MUTATING_PY_PAYMENT_SUM",
    )
    if env is None:
        pytest.skip("Set TEST_KASPI_MUTATING_PHP_PAYMENT_* and _PY_PAYMENT_* in app/.env")

    php_params = {
        "command": "pay",
        "account": int(env["TEST_KASPI_MUTATING_PHP_PAYMENT_ID"]),
        "iin": env["TEST_KASPI_MUTATING_PHP_PAYMENT_IIN"],
        "sum": int(env["TEST_KASPI_MUTATING_PHP_PAYMENT_SUM"]),
        "txn_id": _kaspi_txn_id("pmt-pay-php"),
        "txn_date": _txn_date(),
    }
    py_params = {
        "command": "pay",
        "account": int(env["TEST_KASPI_MUTATING_PY_PAYMENT_ID"]),
        "iin": env["TEST_KASPI_MUTATING_PY_PAYMENT_IIN"],
        "sum": int(env["TEST_KASPI_MUTATING_PY_PAYMENT_SUM"]),
        "txn_id": _kaspi_txn_id("pmt-pay-py"),
        "txn_date": _txn_date(),
    }

    await assert_kaspi_pay_mutating_parity(
        case_id="kaspi-payment-pay-mutating",
        php_action="kaspi-payment-pay",
        py_path="/api/payments/kaspi-payment-pay",
        php_params=php_params,
        py_params=py_params,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
    )


@pytest.mark.asyncio
async def test_cloudpayments_pay_mutating_parity(
    payments_mutating_enabled: None,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    env = _require_env(
        "TEST_CP_MUTATING_PAYMENT_REQUEST_HASH",
        "TEST_CP_MUTATING_PAYMENT_INVOICE_HASH",
        "TEST_CP_MUTATING_PAYMENT_AMOUNT",
    )
    if env is None:
        pytest.skip("Set TEST_CP_MUTATING_PAYMENT_* in app/.env (dedicated unpaid payment)")

    body = (
        f"InvoiceId={env['TEST_CP_MUTATING_PAYMENT_INVOICE_HASH']}"
        f"&Data=%7B%22hash%22%3A%22{env['TEST_CP_MUTATING_PAYMENT_REQUEST_HASH']}%22%7D"
        f"&Amount={env['TEST_CP_MUTATING_PAYMENT_AMOUNT']}"
        f"&TransactionId=tx-cp-pay-{uuid.uuid4().hex[:8]}"
    )

    await assert_cp_mutating_post_parity(
        case_id="cp-pay-mutating",
        mode="pay",
        body=body,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
        expect_code=0,
    )
