"""Unit tests: KaspiService with mocked repository."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.config import payments_config
from src.features.payments.errors import PaymentsDatabaseError

from tests.payments.helpers import kaspi_result, parse_kaspi_xml


@pytest.mark.asyncio
async def test_request_check_coerces_string_query_params(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
    sample_request_info: dict[str, str],
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 0
    kaspi_repo_mock.kaspi_request_get_info.return_value = sample_request_info

    await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params={
            "command": "check",
            "txn_id": "TX-STR",
            "iin": "860515001730",
            "account": "2915844",
            "sum": "100",
        },
    )

    call = kaspi_repo_mock.kaspi_check.await_args
    assert call.args[0] == 2915844
    assert call.args[5] == 100


@pytest.mark.asyncio
async def test_unknown_command_returns_result_5(
    kaspi_service,
    kaspi_allowed_all,
) -> None:
    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params={"command": "invalid", "txn_id": "TX-UNK"},
    )
    assert status == 200
    assert kaspi_result(xml) == "5"


@pytest.mark.asyncio
async def test_forbidden_ip_returns_403(
    kaspi_service,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(payments_config, "kaspi_allowed_ips", ("194.187.247.152",))
    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params={"command": "check", "txn_id": "TX-IP"},
    )
    assert status == 403
    assert kaspi_result(xml) == "403"


@pytest.mark.asyncio
async def test_request_check_success(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
    sample_request_info: dict[str, str],
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 0
    kaspi_repo_mock.kaspi_request_get_info.return_value = sample_request_info

    params = {
        "command": "check",
        "txn_id": "TX-CHK",
        "iin": "860515001730",
        "account": 2915844,
        "sum": 100,
    }
    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params=params,
    )

    assert status == 200
    assert kaspi_result(xml) == "0"
    root = parse_kaspi_xml(xml)
    assert root.find("bin") is not None
    assert root.find("fields") is not None
    kaspi_repo_mock.kaspi_check.assert_awaited_once()
    call = kaspi_repo_mock.kaspi_check.await_args
    assert call.args[4] == 1  # pay_type request
    kaspi_repo_mock.insert_kaspi_pay_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_check_sp_validation_error(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 2

    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params={
            "command": "check",
            "txn_id": "TX-BAD",
            "iin": "000",
            "account": 1,
            "sum": 1,
        },
    )

    assert status == 200
    assert kaspi_result(xml) == "2"
    kaspi_repo_mock.kaspi_request_get_info.assert_not_awaited()
    kaspi_repo_mock.insert_kaspi_pay_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_check_database_error(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
) -> None:
    kaspi_repo_mock.kaspi_check.side_effect = PaymentsDatabaseError("SP failed")

    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params={
            "command": "check",
            "txn_id": "TX-DB",
            "iin": "860515001730",
            "account": 1,
            "sum": 100,
        },
    )

    assert status == 200
    assert kaspi_result(xml) == "5"
    root = parse_kaspi_xml(xml)
    comment = root.find("comment")
    assert comment is not None and comment.text == "SP failed"


@pytest.mark.asyncio
async def test_request_pay_success(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
    sample_request_info: dict[str, str],
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 0
    kaspi_repo_mock.kaspi_request_pay.return_value = 77324
    kaspi_repo_mock.kaspi_request_get_info.return_value = sample_request_info

    params = {
        "command": "pay",
        "txn_id": "TX-PAY",
        "txn_date": "2026-09-09 12:00:00",
        "iin": "860515001730",
        "account": 2915844,
        "sum": 1000,
    }
    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params=params,
    )

    assert status == 200
    assert kaspi_result(xml) == "0"
    root = parse_kaspi_xml(xml)
    assert root.find("prv_txn").text == "77324"  # type: ignore[union-attr]
    kaspi_repo_mock.kaspi_request_pay.assert_awaited_once_with(
        2915844,
        "860515001730",
        1000,
        "TX-PAY",
        "2026-09-09 12:00:00",
    )


@pytest.mark.asyncio
async def test_request_pay_failed_prv_txn(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 0
    kaspi_repo_mock.kaspi_request_pay.return_value = 0

    xml, status = await kaspi_service.handle_request_pay(
        client_ip="127.0.0.1",
        params={
            "command": "pay",
            "txn_id": "TX-FAIL",
            "iin": "860515001730",
            "account": 1,
            "sum": 100,
        },
    )

    assert status == 200
    assert kaspi_result(xml) == "5"
    root = parse_kaspi_xml(xml)
    comment = root.find("comment")
    assert comment is not None and comment.text == "Payment failed"


@pytest.mark.asyncio
async def test_payment_check_uses_pay_type_2(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
    sample_request_info: dict[str, str],
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 0
    kaspi_repo_mock.kaspi_payment_get_info.return_value = {
        **sample_request_info,
        "payment_amount": "5000",
    }

    xml, status = await kaspi_service.handle_payment_pay(
        client_ip="127.0.0.1",
        params={
            "command": "check",
            "txn_id": "TX-P2",
            "iin": "860515001730",
            "account": 77821,
            "sum": 5000,
        },
    )

    assert status == 200
    assert kaspi_result(xml) == "0"
    root = parse_kaspi_xml(xml)
    assert root.find("sum") is not None
    call = kaspi_repo_mock.kaspi_check.await_args
    assert call.args[0] is None  # client_request_id
    assert call.args[1] == 77821  # client_request_payment_id
    assert call.args[4] == 2  # pay_type payment


@pytest.mark.asyncio
async def test_payment_pay_success(
    kaspi_service,
    kaspi_repo_mock: AsyncMock,
    kaspi_allowed_all,
    sample_request_info: dict[str, str],
) -> None:
    kaspi_repo_mock.kaspi_check.return_value = 0
    kaspi_repo_mock.kaspi_payment_pay.return_value = 99001
    kaspi_repo_mock.kaspi_payment_get_info.return_value = sample_request_info

    xml, status = await kaspi_service.handle_payment_pay(
        client_ip="127.0.0.1",
        params={
            "command": "pay",
            "txn_id": "TX-PP",
            "iin": "860515001730",
            "account": 77821,
            "sum": 100,
        },
    )

    assert status == 200
    root = parse_kaspi_xml(xml)
    assert root.find("prv_txn").text == "99001"  # type: ignore[union-attr]
    kaspi_repo_mock.kaspi_payment_pay.assert_awaited_once_with(
        77821,
        "860515001730",
        100,
        "TX-PP",
    )
