from src.pg_error_utils import clean_postgres_error_message, find_postgres_error


class WorkersDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_workers_database_error(exc: Exception) -> WorkersDatabaseError:
    pg_error = find_postgres_error(exc)
    if pg_error is not None:
        return WorkersDatabaseError(clean_postgres_error_message(pg_error))
    return WorkersDatabaseError(str(exc))
