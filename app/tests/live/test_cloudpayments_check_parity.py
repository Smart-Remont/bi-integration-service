"""Live parity: CloudPayments check — PHP devprod vs integrations-sr.

Optional env for valid check:
  TEST_CP_REQUEST_HASH, TEST_CP_INVOICE_HASH

Run:
  uv run pytest app/tests/live/test_cloudpayments_check_parity.py -m payments_parity -v
"""

from __future__ import annotations

import httpx
import pytest

from .payments_parity_helpers import (
    CloudPaymentsParityCase,
    assert_cloudpayments_post_parity,
    cp_env_snapshot,
    resolve_cp_body,
)

pytestmark = [pytest.mark.live, pytest.mark.parity, pytest.mark.payments_parity]

CP_CHECK_CASES: tuple[CloudPaymentsParityCase, ...] = (
    CloudPaymentsParityCase(
        id="cp-check-empty-body",
        mode="check",
        body="",
    ),
    CloudPaymentsParityCase(
        id="cp-check-invalid-hash-empty",
        mode="check",
        body="InvoiceId=&Data=",
    ),
    CloudPaymentsParityCase(
        id="cp-check-invalid-hash-bad-json",
        mode="check",
        body="InvoiceId=bad&Data=not-json&Amount=100&TransactionId=tx-bad",
    ),
    CloudPaymentsParityCase(
        id="cp-check-invalid-hash",
        mode="check",
        body=(
            "InvoiceId=inv-bad&Data=%7B%22hash%22%3A%22badhash%22%7D"
            "&Amount=100&TransactionId=tx-invalid"
        ),
    ),
    CloudPaymentsParityCase(
        id="cp-check-valid-fixture",
        mode="check",
        body=(
            "InvoiceId=__INVOICE_HASH__&Data=%7B%22hash%22%3A%22__REQUEST_HASH__%22%7D"
            "&Amount=__AMOUNT__&TransactionId=tx-valid"
        ),
        required_env=(
            ("__REQUEST_HASH__", "TEST_CP_REQUEST_HASH"),
            ("__INVOICE_HASH__", "TEST_CP_INVOICE_HASH"),
            ("__AMOUNT__", "TEST_CP_AMOUNT"),
        ),
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


@pytest.mark.parametrize("case", CP_CHECK_CASES, ids=lambda c: c.id)
@pytest.mark.asyncio
async def test_cloudpayments_check_parity(
    case: CloudPaymentsParityCase,
    office_base_url: str,
    integrations_base_url: str,
    payments_parity_client: httpx.AsyncClient,
) -> None:
    body = resolve_cp_body(case, env=cp_env_snapshot())
    if body is None:
        missing = [env_name for _, env_name in case.required_env]
        pytest.skip(f"Set env for case {case.id}: {missing}")

    await assert_cloudpayments_post_parity(
        case=case,
        body=body,
        office_base_url=office_base_url,
        integrations_base_url=integrations_base_url,
        client=payments_parity_client,
    )
