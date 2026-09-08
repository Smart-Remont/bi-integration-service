"""Shared PostgreSQL error-message parsing, used by feature-specific error modules.

Stored functions raise ``RAISE EXCEPTION '{human-readable message}'`` — the curly
braces are a convention from the legacy PHP layer, kept so SP error text does not
need to change during the cutover. This module extracts just that text.
"""

import re
from typing import TypeVar

from asyncpg.exceptions import PostgresError

_RAISE_MESSAGE_RE = re.compile(r"\{([^}]*)\}")
DatabaseErrorT = TypeVar("DatabaseErrorT", bound=Exception)


def clean_postgres_error_message(exc: PostgresError) -> str:
    """Extract the ``{...}`` payload from a SP ``RAISE EXCEPTION``, else raw text."""
    text = str(exc)
    match = _RAISE_MESSAGE_RE.search(text)
    if match:
        return match.group(1)
    return text


def find_postgres_error(exc: BaseException) -> PostgresError | None:
    """Walk ``__cause__`` chain to find the first ``PostgresError``, if any."""
    cause: BaseException | None = exc
    while cause is not None:
        if isinstance(cause, PostgresError):
            return cause
        cause = cause.__cause__
    return None


def map_to_database_error(exc: Exception, error_type: type[DatabaseErrorT]) -> DatabaseErrorT:
    """Map asyncpg exception chains to a feature-specific DB error class."""
    pg_error = find_postgres_error(exc)
    if pg_error is not None:
        return error_type(clean_postgres_error_message(pg_error))
    return error_type(str(exc))
