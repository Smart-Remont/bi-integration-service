"""Normalization of optional query parameters before SP calls."""


def zero_to_null(value: object | None) -> object | None:
    """
    Convert empty or zero sentinel values to ``None`` for PostgreSQL.

    Treats ``""``, ``"0"``, and integer ``0`` as absent; other values pass through.
    """
    if value is None:
        return None
    if value == "0" or value == "" or value == 0:
        return None
    return value
