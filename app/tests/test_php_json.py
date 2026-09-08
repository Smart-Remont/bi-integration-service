from __future__ import annotations

import datetime
from decimal import Decimal

from src.php_json import php_jsonable_encoder


def test_datetime_uses_space_not_iso_t() -> None:
    value = datetime.datetime(2026, 9, 4, 23, 14, 33)
    assert php_jsonable_encoder(value) == "2026-09-04 23:14:33"


def test_datetime_with_microseconds() -> None:
    value = datetime.datetime(2026, 4, 23, 14, 58, 12, 702613)
    assert php_jsonable_encoder(value) == "2026-04-23 14:58:12.702613"


def test_datetime_trims_trailing_microsecond_zeros() -> None:
    value = datetime.datetime(2022, 7, 20, 15, 45, 37, 476000)
    assert php_jsonable_encoder(value) == "2022-07-20 15:45:37.476"


def test_date_uses_yyyy_mm_dd() -> None:
    value = datetime.date(2025, 12, 30)
    assert php_jsonable_encoder(value) == "2025-12-30"


def test_float_zero_becomes_string_zero() -> None:
    assert php_jsonable_encoder(0.0) == "0"


def test_float_with_fraction_becomes_string() -> None:
    assert php_jsonable_encoder(33.13) == "33.13"


def test_decimal_strips_trailing_zeros() -> None:
    assert php_jsonable_encoder(Decimal("33.130000")) == "33.13"


def test_nested_row_like_sp_output() -> None:
    row = {
        "request_date": datetime.datetime(2026, 9, 4, 23, 14, 33),
        "client_request_id": 3218083,
        "terrace_area": 0.0,
        "is_active": 1,
        "is_another": True,
    }
    assert php_jsonable_encoder(row) == {
        "request_date": "2026-09-04 23:14:33",
        "client_request_id": 3218083,
        "terrace_area": "0",
        "is_active": 1,
        "is_another": True,
    }
