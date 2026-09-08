from src.pg_error_utils import map_to_database_error


class PaymentsDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_payments_database_error(exc: Exception) -> PaymentsDatabaseError:
    return map_to_database_error(exc, PaymentsDatabaseError)
