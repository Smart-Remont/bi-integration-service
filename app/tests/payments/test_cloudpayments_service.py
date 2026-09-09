"""Unit tests: CloudPaymentsService with mocked repository."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from src.features.payments.cloud_payments.service import CloudPaymentsService
from src.features.payments.errors import PaymentsDatabaseError

from tests.payments.cp_helpers import cp_request


@pytest.fixture
def cp_repo_mock() -> AsyncMock:
    repo = AsyncMock()
    repo.cloud_payments_pay = AsyncMock(return_value=None)
    repo.payment_client_request_get = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def cp_service(cp_repo_mock: AsyncMock) -> CloudPaymentsService:
    return CloudPaymentsService(cp_repo_mock)


@pytest.mark.asyncio
async def test_parse_body_urlencoded(cp_service: CloudPaymentsService) -> None:
    request = await cp_request(
        b"Data=%7B%22hash%22%3A%22abc%22%7D&InvoiceId=inv1&Amount=500&TransactionId=tx1",
    )
    payload = await cp_service._parse_body(request)
    assert payload == {
        "Data": '{"hash":"abc"}',
        "InvoiceId": "inv1",
        "Amount": "500",
        "TransactionId": "tx1",
    }


@pytest.mark.asyncio
async def test_parse_body_empty_returns_empty_dict(cp_service: CloudPaymentsService) -> None:
    request = await cp_request(b"")
    assert await cp_service._parse_body(request) == {}


def test_extract_request_hash_from_json_data(cp_service: CloudPaymentsService) -> None:
    assert cp_service._extract_request_hash({"Data": '{"hash":"req-hash"}'}) == "req-hash"


def test_extract_request_hash_missing_data(cp_service: CloudPaymentsService) -> None:
    assert cp_service._extract_request_hash({}) == ""


def test_extract_request_hash_invalid_json_uses_raw(cp_service: CloudPaymentsService) -> None:
    assert cp_service._extract_request_hash({"Data": "plain-text"}) == "plain-text"


@pytest.mark.asyncio
async def test_check_mode_returns_sp_code_including_null(
    cp_service: CloudPaymentsService,
    cp_repo_mock: AsyncMock,
) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = None
    request = await cp_request(b"InvoiceId=&Data=")

    response = await cp_service.handle("check", request)

    assert response.status_code == 200
    assert json.loads(response.body) == {"code": None}
    cp_repo_mock.cloud_payments_pay.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_mode_success(cp_service: CloudPaymentsService, cp_repo_mock: AsyncMock) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = 0
    request = await cp_request(
        b"Data=%7B%22hash%22%3A%22ok%22%7D&InvoiceId=inv&Amount=100&TransactionId=tx",
    )

    response = await cp_service.handle("check", request)

    assert json.loads(response.body) == {"code": 0}


@pytest.mark.asyncio
async def test_sp_exception_returns_code_13(
    cp_service: CloudPaymentsService,
    cp_repo_mock: AsyncMock,
) -> None:
    cp_repo_mock.cloud_payments_pay.side_effect = PaymentsDatabaseError("SP failed")
    request = await cp_request(b"InvoiceId=x&Data=%7B%22hash%22%3A%22y%22%7D")

    response = await cp_service.handle("check", request)

    assert json.loads(response.body) == {"code": 13}


@pytest.mark.asyncio
async def test_pay_mode_success(cp_service: CloudPaymentsService, cp_repo_mock: AsyncMock) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = 5
    cp_repo_mock.payment_client_request_get.return_value = {"payment_amount": 100}
    request = await cp_request(
        b"Data=%7B%22hash%22%3A%22ok%22%7D&InvoiceId=inv&Amount=100&TransactionId=tx",
    )

    response = await cp_service.handle("pay", request)

    assert json.loads(response.body) == {"code": 5}
    cp_repo_mock.payment_client_request_get.assert_awaited_once()


@pytest.mark.asyncio
async def test_pay_mode_zero_code_is_success(
    cp_service: CloudPaymentsService,
    cp_repo_mock: AsyncMock,
) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = 0
    cp_repo_mock.payment_client_request_get.return_value = {"payment_amount": 100}
    request = await cp_request(b"InvoiceId=inv&Data=%7B%22hash%22%3A%22x%22%7D")

    response = await cp_service.handle("pay", request)

    assert json.loads(response.body) == {"code": 0}


@pytest.mark.asyncio
async def test_fail_mode_success(cp_service: CloudPaymentsService, cp_repo_mock: AsyncMock) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = 2
    request = await cp_request(b"InvoiceId=inv&Data=%7B%22hash%22%3A%22x%22%7D")

    response = await cp_service.handle("fail", request)

    assert json.loads(response.body) == {"code": 2}


@pytest.mark.asyncio
async def test_fail_mode_zero_code_is_success(
    cp_service: CloudPaymentsService,
    cp_repo_mock: AsyncMock,
) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = 0
    request = await cp_request(b"InvoiceId=inv&Data=%7B%22hash%22%3A%22x%22%7D")

    response = await cp_service.handle("fail", request)

    assert json.loads(response.body) == {"code": 0}


@pytest.mark.asyncio
async def test_unknown_mode_returns_13(cp_service: CloudPaymentsService, cp_repo_mock: AsyncMock) -> None:
    cp_repo_mock.cloud_payments_pay.return_value = 0
    request = await cp_request(b"InvoiceId=inv&Data=%7B%22hash%22%3A%22x%22%7D")

    response = await cp_service.handle("unknown", request)

    assert json.loads(response.body) == {"code": 13}
