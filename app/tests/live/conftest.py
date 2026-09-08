"""Pytest hooks for live parity tests."""

from __future__ import annotations

import pytest

from .parity_reporter import parity_log_dir


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
