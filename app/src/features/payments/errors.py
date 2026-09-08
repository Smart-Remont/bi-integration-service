from src.pg_error_utils import clean_postgres_error_message, find_postgres_error


class PaymentsDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_payments_database_error(exc: Exception) -> PaymentsDatabaseError:
    pg_error = find_postgres_error(exc)
    if pg_error is not None:
        return PaymentsDatabaseError(clean_postgres_error_message(pg_error))
    return PaymentsDatabaseError(str(exc))
