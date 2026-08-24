import re
from collections.abc import Generator
from contextlib import contextmanager

from asyncpg.exceptions import (
    CheckViolationError,
    ForeignKeyViolationError,
    IntegrityConstraintViolationError,
    PostgresError,
    UndefinedColumnError,
    UndefinedTableError,
    UniqueViolationError,
)

from .infra import (
    CheckConstraintError,
    DatabaseConfigurationError,
    DataIntegrityError,
    DuplicateKeyError,
    ForeignKeyError,
    InfrastructureError,
    StoredProcedureError,
    UnexpectedDatabaseError,
)

_PG_RAISE_MESSAGE_RE = re.compile(r"\{([^}]*)\}")


def clean_postgres_raise_message(exc: Exception) -> str:
    text = str(exc)
    match = _PG_RAISE_MESSAGE_RE.search(text)
    return match.group(1).strip() if match else text


@contextmanager
def map_asyncpg_errors() -> Generator[None, None, None]:
    try:
        yield

    except UniqueViolationError as e:
        raise DuplicateKeyError() from e

    except ForeignKeyViolationError as e:
        raise ForeignKeyError() from e

    except CheckViolationError as e:
        raise CheckConstraintError() from e

    except IntegrityConstraintViolationError as e:
        raise DataIntegrityError() from e

    except (UndefinedColumnError, UndefinedTableError) as e:
        raise DatabaseConfigurationError() from e

    except InfrastructureError:
        raise

    except PostgresError as e:
        sqlstate = getattr(e, "sqlstate", None)
        if sqlstate == "P0001" or _PG_RAISE_MESSAGE_RE.search(str(e)):
            raise StoredProcedureError(clean_postgres_raise_message(e)) from e
        raise UnexpectedDatabaseError() from e
