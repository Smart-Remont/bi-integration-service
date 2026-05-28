import re

from asyncpg.exceptions import PostgresError

_PG_RAISE_MESSAGE_RE = re.compile(r"\{([^}]*)\}")


class BigIntegrationDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def clean_postgres_error_message(exc: PostgresError) -> str:
    text = str(exc)
    match = _PG_RAISE_MESSAGE_RE.search(text)
    if match:
        return match.group(1)
    return text


def to_big_integration_database_error(exc: Exception) -> BigIntegrationDatabaseError:
    cause: BaseException | None = exc
    while cause is not None:
        if isinstance(cause, PostgresError):
            return BigIntegrationDatabaseError(clean_postgres_error_message(cause))
        cause = cause.__cause__
    return BigIntegrationDatabaseError(str(exc))
