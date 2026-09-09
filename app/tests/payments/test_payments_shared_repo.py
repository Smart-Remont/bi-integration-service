"""Unit tests: PaymentsRepository helpers."""

from __future__ import annotations

from src.features.payments.shared_repo import PaymentsRepository


def test_bank_info_json_none() -> None:
    assert PaymentsRepository.bank_info_json(None) == ""


def test_bank_info_json_object() -> None:
    assert PaymentsRepository.bank_info_json({"bankName": "Sber"}) == '{"bankName": "Sber"}'
