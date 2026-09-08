from src.pg_error_utils import map_to_database_error


class LeadsDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_leads_database_error(exc: Exception) -> LeadsDatabaseError:
    return map_to_database_error(exc, LeadsDatabaseError)
