"""Shared PostgreSQL error-message parsing, used by feature-specific error modules.

Stored functions raise ``RAISE EXCEPTION '{human-readable message}'`` — the curly
braces are a convention from the legacy PHP layer, kept so SP error text does not
need to change during the cutover. This module extracts just that text.
"""

import re

from asyncpg.exceptions import PostgresError

_RAISE_MESSAGE_RE = re.compile(r"\{([^}]*)\}")


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
