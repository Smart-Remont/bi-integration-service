__all__ = (
    "CheckConstraintError",
    "DataIntegrityError",
    "DatabaseConfigurationError",
    "DuplicateKeyError",
    "ForeignKeyError",
    "InfrastructureError",
    "StoredProcedureError",
    "UnexpectedDatabaseError",
)


class InfrastructureError(Exception):
    """Persistence / database infrastructure failures."""


class DuplicateKeyError(InfrastructureError):
    """A unique constraint was violated."""


class ForeignKeyError(InfrastructureError):
    """A foreign key constraint was violated."""


class CheckConstraintError(InfrastructureError):
    """A check constraint was violated."""


class DataIntegrityError(InfrastructureError):
    """A generic integrity constraint was violated."""


class DatabaseConfigurationError(InfrastructureError):
    """The database schema does not match expectations (e.g. missing table/column)."""


class UnexpectedDatabaseError(InfrastructureError):
    """An unexpected database error occurred."""


class StoredProcedureError(InfrastructureError):
    """Business rule raised from PostgreSQL RAISE EXCEPTION '{...}'."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
