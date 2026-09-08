"""Encode SP row values like legacy PHP (PDO fetch + json_encode)."""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def _datetime_to_php_str(value: datetime.datetime) -> str:
    text = value.strftime("%Y-%m-%d %H:%M:%S")
    if value.microsecond:
        frac = f".{value.microsecond:06d}".rstrip("0")
        text += frac
    return text


def php_jsonable_encoder(obj: Any) -> Any:
    """Recursively normalize asyncpg/Python values to PHP JSON shapes."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {key: php_jsonable_encoder(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [php_jsonable_encoder(item) for item in obj]
    if isinstance(obj, tuple):
        return [php_jsonable_encoder(item) for item in obj]
    if isinstance(obj, datetime.datetime):
        return _datetime_to_php_str(obj)
    if isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, datetime.time):
        return obj.strftime("%H:%M:%S")
    if isinstance(obj, Decimal):
        return _decimal_to_php_str(obj)
    if isinstance(obj, float):
        return _float_to_php_str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8")
    if isinstance(obj, (str, int, bool)):
        return obj
    return obj


def _decimal_to_php_str(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _float_to_php_str(value: float) -> str:
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    text = format(value, "f").rstrip("0").rstrip(".")
    return text or "0"
