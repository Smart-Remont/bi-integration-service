from src.pg_error_utils import map_to_database_error


class WorkersDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_workers_database_error(exc: Exception) -> WorkersDatabaseError:
    return map_to_database_error(exc, WorkersDatabaseError)
