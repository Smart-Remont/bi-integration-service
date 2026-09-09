"""Unit tests: SberbankCallbackService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.features.payments.sberbank_callback.service import SberbankCallbackService
from src.features.payments.shared_repo import PaymentsRepository


@pytest.fixture
def sber_mock() -> AsyncMock:
    sber = AsyncMock()
    sber.get_order_status_extended = AsyncMock(
        return_value={"bankInfo": {"bankName": "Test"}, "actionCode": 0},
    )
    return sber


@pytest.fixture
def repo_mock() -> AsyncMock:
    repo = AsyncMock(spec=PaymentsRepository)
    repo.payment_client_request_get_by_id = AsyncMock(return_value=None)
    repo.insert_sberbank_pay_log = AsyncMock(return_value=None)
    repo.sberbank_client_request_payment_set = AsyncMock(return_value=None)
    repo.sberbank_transaction_set = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def callback_service(repo_mock: AsyncMock, sber_mock: AsyncMock) -> SberbankCallbackService:
    return SberbankCallbackService(repo_mock, sber_mock)


@pytest.mark.asyncio
async def test_no_order_number_returns_zero(callback_service: SberbankCallbackService, repo_mock: AsyncMock) -> None:
    assert await callback_service.handle({}) == "0"
    repo_mock.payment_client_request_get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_order_returns_zero(callback_service: SberbankCallbackService, repo_mock: AsyncMock) -> None:
    assert await callback_service.handle({"orderNumber": "999999999"}) == "0"
    repo_mock.payment_client_request_get_by_id.assert_awaited_once_with(999999999)


@pytest.mark.asyncio
async def test_deposited_status_1_sets_payment(
    callback_service: SberbankCallbackService,
    repo_mock: AsyncMock,
    sber_mock: AsyncMock,
) -> None:
    repo_mock.payment_client_request_get_by_id.return_value = {
        "client_request_id": 100,
        "payment_amount": 1000,
    }

    result = await callback_service.handle(
        {
            "orderNumber": "77821",
            "operation": "deposited",
            "status": "1",
            "mdOrder": "md-1",
        },
    )

    assert result == "0"
    repo_mock.insert_sberbank_pay_log.assert_awaited_once()
    sber_mock.get_order_status_extended.assert_awaited_once_with("md-1", 77821)
    repo_mock.sberbank_client_request_payment_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_deposited_status_not_1_sets_transaction(
    callback_service: SberbankCallbackService,
    repo_mock: AsyncMock,
    sber_mock: AsyncMock,
) -> None:
    repo_mock.payment_client_request_get_by_id.return_value = {
        "client_request_id": 100,
        "payment_amount": 500,
    }

    result = await callback_service.handle(
        {
            "orderNumber": 77821,
            "operation": "deposited",
            "status": "0",
        },
    )

    assert result == "0"
    sber_mock.get_order_status_extended.assert_not_awaited()
    repo_mock.sberbank_transaction_set.assert_awaited_once_with(77821, 100, None)


@pytest.mark.asyncio
async def test_non_deposited_only_logs(
    callback_service: SberbankCallbackService,
    repo_mock: AsyncMock,
    sber_mock: AsyncMock,
) -> None:
    repo_mock.payment_client_request_get_by_id.return_value = {
        "client_request_id": 100,
        "payment_amount": 500,
    }

    assert await callback_service.handle({"orderNumber": "1", "operation": "approved"}) == "0"
    repo_mock.insert_sberbank_pay_log.assert_awaited_once()
    repo_mock.sberbank_transaction_set.assert_not_awaited()
    repo_mock.sberbank_client_request_payment_set.assert_not_awaited()
