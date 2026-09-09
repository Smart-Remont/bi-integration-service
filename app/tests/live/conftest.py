"""Pytest hooks and fixtures for live parity tests."""

from __future__ import annotations

import os

import pytest

from .parity_reporter import parity_log_dir


@pytest.fixture
def parity_mutating_enabled() -> None:
    """Opt-in gate for tests that mutate devprod data."""
    if os.getenv("PARITY_MUTATING", "").strip() != "1":
        pytest.skip("Set PARITY_MUTATING=1 to run mutating parity tests")


@pytest.fixture
def payments_mutating_enabled() -> None:
    """Opt-in gate for Payments write parity (Kaspi pay, CP pay, Sber callback)."""
    if os.getenv("PAYMENTS_MUTATING", "").strip() != "1":
        pytest.skip("Set PAYMENTS_MUTATING=1 to run payments mutating parity tests")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    log_dir = parity_log_dir()
    if log_dir is None:
        return
    # Only mention logs when parity tests were collected.
    if not session.config.getoption("markexpr", default=""):
        return
    if "parity" not in str(session.config.getoption("markexpr", default="")):
        return
    print(f"\nParity logs written to: {log_dir.resolve()}")
