from src.pg_error_utils import clean_postgres_error_message, find_postgres_error

_KNOWN_BI_ERROR_CODES = frozenset(
    {"P001", "P002", "P004", "P005", "P006", "P007", "P008", "P009", "P010", "P011", "P012", "P013", "P014"},
)
_FALLBACK_BI_ERROR_CODE = "P400"


class BiDatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def to_bi_database_error(exc: Exception) -> BiDatabaseError:
    pg_error = find_postgres_error(exc)
    if pg_error is not None:
        return BiDatabaseError(clean_postgres_error_message(pg_error))
    return BiDatabaseError(str(exc))


def bi_error_code(message: str) -> str:
    """
    First 4 chars of the SP error message, if it's a known ``P0xx`` code.

    Mirrors legacy PHP ``_getBiErrorCode()``: stored functions in this domain
    raise ``RAISE EXCEPTION '{P0xx human text}'`` — the leading code becomes the
    ``data`` field of the error envelope, distinct from ``error.message``.
    """
    code = message[:4]
    if code in _KNOWN_BI_ERROR_CODES:
        return code
    return _FALLBACK_BI_ERROR_CODE
