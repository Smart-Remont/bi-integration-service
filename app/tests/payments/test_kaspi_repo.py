"""Unit tests: KaspiRepository call_sp wiring (no PostgreSQL)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.features.payments.constants import CLIENT_MODULE_CODE, PUBLIC_MODULE_CODE
from src.features.payments.kaspi.repo import KaspiRepository


@pytest.fixture
def kaspi_repo() -> KaspiRepository:
    repo = KaspiRepository(MagicMock())
    repo.call_sp = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_kaspi_check_request_pay_type_1(kaspi_repo: KaspiRepository) -> None:
    kaspi_repo.call_sp.return_value = [{"kaspi_check": 0}]

    result = await kaspi_repo.kaspi_check(
        2915844,
        None,
        "860515001730",
        "check",
        1,
        100,
        "TX-REQ",
    )

    assert result == 0
    kaspi_repo.call_sp.assert_awaited_once_with(
        "client.kaspi_check",
        2915844,
        None,
        "860515001730",
        "check",
        1,
        100,
        "TX-REQ",
        module_code=CLIENT_MODULE_CODE,
    )


@pytest.mark.asyncio
async def test_kaspi_check_payment_pay_type_2(kaspi_repo: KaspiRepository) -> None:
    kaspi_repo.call_sp.return_value = [{"kaspi_check": 2}]

    result = await kaspi_repo.kaspi_check(
        None,
        77821,
        "860515001730",
        "pay",
        2,
        5000,
        "TX-PAY",
    )

    assert result == 2
    kaspi_repo.call_sp.assert_awaited_once_with(
        "client.kaspi_check",
        None,
        77821,
        "860515001730",
        "pay",
        2,
        5000,
        "TX-PAY",
        module_code=CLIENT_MODULE_CODE,
    )


@pytest.mark.asyncio
async def test_kaspi_request_get_info_uses_refcursor(kaspi_repo: KaspiRepository) -> None:
    kaspi_repo.call_sp.return_value = [{"prop_fio": "Test User"}]

    row = await kaspi_repo.kaspi_request_get_info(2915844, "860515001730")

    assert row == {"prop_fio": "Test User"}
    kaspi_repo.call_sp.assert_awaited_once_with(
        "client.kaspi_request_get_info",
        2915844,
        "860515001730",
        cursor=True,
        module_code=CLIENT_MODULE_CODE,
    )


@pytest.mark.asyncio
async def test_kaspi_request_pay_triggers_after_payment_operations(
    kaspi_repo: KaspiRepository,
) -> None:
    kaspi_repo.call_sp = AsyncMock(
        side_effect=[
            [{"client_request_payment_id": 77324}],
            None,
        ]
    )

    payment_id = await kaspi_repo.kaspi_request_pay(
        2915844,
        "860515001730",
        1000,
        "TX-PAY-OK",
        "2026-09-09 12:00:00",
    )

    assert payment_id == 77324
    assert kaspi_repo.call_sp.await_count == 2
    kaspi_repo.call_sp.assert_any_await(
        "client.kaspi_request_pay",
        2915844,
        "860515001730",
        1000,
        "TX-PAY-OK",
        "2026-09-09 12:00:00",
        module_code=CLIENT_MODULE_CODE,
    )
    kaspi_repo.call_sp.assert_any_await(
        "public.after_payment_operations",
        77324,
        module_code=PUBLIC_MODULE_CODE,
    )


@pytest.mark.asyncio
async def test_kaspi_request_pay_zero_skips_after_payment(
    kaspi_repo: KaspiRepository,
) -> None:
    kaspi_repo.call_sp.return_value = [{"client_request_payment_id": 0}]

    payment_id = await kaspi_repo.kaspi_request_pay(
        1,
        "860515001730",
        100,
        "TX-FAIL",
        None,
    )

    assert payment_id == 0
    kaspi_repo.call_sp.assert_awaited_once()


@pytest.mark.asyncio
async def test_insert_kaspi_pay_log(kaspi_repo: KaspiRepository) -> None:
    await kaspi_repo.insert_kaspi_pay_log(
        kaspi_what="check",
        response_in='{"command":"check"}',
        response_out="<response/>",
        account=2915844,
        txn_id="TX-LOG",
        sum_value=100,
        txn_date=None,
        pay_type=1,
        kaspi_pay_status=1,
    )

    kaspi_repo.call_sp.assert_awaited_once_with(
        "client.insert_kaspi_pay_log",
        "check",
        '{"command":"check"}',
        "<response/>",
        2915844,
        "TX-LOG",
        100,
        None,
        1,
        1,
        module_code=CLIENT_MODULE_CODE,
    )
