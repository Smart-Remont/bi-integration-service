"""Unit tests: SberbankCheckStatusService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.features.payments.sberbank_check_status.service import SberbankCheckStatusService
from src.features.payments.shared_repo import PaymentsRepository


@pytest.fixture
def sber_mock() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repo_mock() -> AsyncMock:
    repo = AsyncMock(spec=PaymentsRepository)
    repo.sberbank_payment_read_for_status = AsyncMock(return_value=[])
    repo.sberbank_client_request_payment_set = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def cron_service(repo_mock: AsyncMock, sber_mock: AsyncMock) -> SberbankCheckStatusService:
    return SberbankCheckStatusService(repo_mock, sber_mock)


@pytest.mark.asyncio
async def test_empty_pending_returns_zero(
    cron_service: SberbankCheckStatusService,
    sber_mock: AsyncMock,
) -> None:
    assert await cron_service.poll() == "0"
    sber_mock.get_order_status_extended.assert_not_awaited()


@pytest.mark.asyncio
async def test_successful_poll_updates_payment(
    cron_service: SberbankCheckStatusService,
    repo_mock: AsyncMock,
    sber_mock: AsyncMock,
) -> None:
    repo_mock.sberbank_payment_read_for_status.return_value = [
        {
            "client_request_id": 100,
            "client_request_payment_id": 77821,
            "cp_transaction_id": "tx-1",
        },
    ]
    sber_mock.get_order_status_extended.return_value = {
        "actionCode": 0,
        "orderNumber": 77821,
        "attributes": [{"value": "attr-tx"}],
        "bankInfo": {"bankName": "Sber"},
    }

    assert await cron_service.poll() == "0"
    sber_mock.get_order_status_extended.assert_awaited_once()
    repo_mock.sberbank_client_request_payment_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_zero_action_code_skips_update(
    cron_service: SberbankCheckStatusService,
    repo_mock: AsyncMock,
    sber_mock: AsyncMock,
) -> None:
    repo_mock.sberbank_payment_read_for_status.return_value = [
        {"client_request_id": 100, "client_request_payment_id": 1, "cp_transaction_id": "tx"},
    ]
    sber_mock.get_order_status_extended.return_value = {"actionCode": 5, "orderNumber": 1}

    assert await cron_service.poll() == "0"
    repo_mock.sberbank_client_request_payment_set.assert_not_awaited()
