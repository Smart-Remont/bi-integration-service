from src.pg_error_utils import clean_postgres_error_message, find_postgres_error


class SigningDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_signing_database_error(exc: Exception) -> SigningDatabaseError:
    pg_error = find_postgres_error(exc)
    if pg_error is not None:
        return SigningDatabaseError(clean_postgres_error_message(pg_error))
    return SigningDatabaseError(str(exc))
