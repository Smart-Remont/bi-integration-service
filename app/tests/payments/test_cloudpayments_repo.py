"""Unit tests: CloudPaymentsRepository call_sp wiring."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.features.payments.cloud_payments.repo import CloudPaymentsRepository
from src.features.payments.constants import CLIENT_MODULE_CODE


@pytest.fixture
def cp_repo() -> CloudPaymentsRepository:
    repo = CloudPaymentsRepository(MagicMock())
    repo.call_sp = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_cloud_payments_pay_call_sp_args(cp_repo: CloudPaymentsRepository) -> None:
    cp_repo.call_sp.return_value = [{"code": 0}]

    result = await cp_repo.cloud_payments_pay(
        "check",
        "req-hash",
        "pay-hash",
        100,
        '{"InvoiceId":"pay-hash"}',
        "tx-1",
    )

    assert result == 0
    cp_repo.call_sp.assert_awaited_once_with(
        "client.cloud_payments_pay",
        "check",
        "req-hash",
        "pay-hash",
        100,
        '{"InvoiceId":"pay-hash"}',
        "tx-1",
        module_code=CLIENT_MODULE_CODE,
    )


@pytest.mark.asyncio
async def test_cloud_payments_pay_null_scalar(cp_repo: CloudPaymentsRepository) -> None:
    cp_repo.call_sp.return_value = [{"code": None}]

    result = await cp_repo.cloud_payments_pay("check", "", "", 0, "{}", "")

    assert result is None


def test_cp_response_json() -> None:
    payload = {"InvoiceId": "inv", "Amount": "100"}
    assert CloudPaymentsRepository.cp_response_json(payload) == '{"InvoiceId": "inv", "Amount": "100"}'
