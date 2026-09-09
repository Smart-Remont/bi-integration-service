"""Unit tests: SberbankPayService (register dry paths)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.responses import PlainTextResponse, RedirectResponse

from src.features.payments.sberbank_pay.service import SberbankPayService
from src.features.payments.shared_repo import PaymentsRepository


@pytest.fixture
def sber_mock() -> AsyncMock:
    sber = AsyncMock()
    sber.register = AsyncMock(return_value={"formUrl": "https://sber.example/pay", "orderId": "o1"})
    return sber


@pytest.fixture
def repo_mock() -> AsyncMock:
    repo = AsyncMock(spec=PaymentsRepository)
    repo.sberbank_check = AsyncMock(return_value=None)
    repo.insert_sberbank_pay_log = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def pay_service(repo_mock: AsyncMock, sber_mock: AsyncMock) -> SberbankPayService:
    return SberbankPayService(repo_mock, sber_mock)


@pytest.mark.asyncio
async def test_register_without_hash_returns_400(pay_service: SberbankPayService) -> None:
    response = await pay_service.handle("register", None, None, "http://test", {})

    assert isinstance(response, PlainTextResponse)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_payment_not_found(pay_service: SberbankPayService, repo_mock: AsyncMock) -> None:
    response = await pay_service.handle(
        "register",
        "req-hash",
        "pay-hash",
        "http://test",
        {},
    )

    assert isinstance(response, PlainTextResponse)
    assert response.body.decode() == "Платеж не найден"
    repo_mock.sberbank_check.assert_awaited_once_with("pay-hash", "req-hash")


@pytest.mark.asyncio
async def test_register_success_redirect(
    pay_service: SberbankPayService,
    repo_mock: AsyncMock,
    sber_mock: AsyncMock,
) -> None:
    repo_mock.sberbank_check.return_value = {
        "client_request_id": 100,
        "client_request_payment_id": 77821,
        "payment_amount": 1000,
    }

    response = await pay_service.handle(
        "register",
        "req-hash",
        "pay-hash",
        "http://test",
        {},
    )

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 302
    sber_mock.register.assert_awaited_once()
