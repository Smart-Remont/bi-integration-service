from src.pg_error_utils import map_to_database_error


class SigningDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_signing_database_error(exc: Exception) -> SigningDatabaseError:
    return map_to_database_error(exc, SigningDatabaseError)
