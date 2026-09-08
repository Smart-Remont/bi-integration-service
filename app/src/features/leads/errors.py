from src.pg_error_utils import clean_postgres_error_message, find_postgres_error


class LeadsDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_leads_database_error(exc: Exception) -> LeadsDatabaseError:
    pg_error = find_postgres_error(exc)
    if pg_error is not None:
        return LeadsDatabaseError(clean_postgres_error_message(pg_error))
    return LeadsDatabaseError(str(exc))
