from src.pg_error_utils import map_to_database_error


class SmsDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_sms_database_error(exc: Exception) -> SmsDatabaseError:
    return map_to_database_error(exc, SmsDatabaseError)
