from src.repository.base import SpRows


def scalar_from_sp_rows(rows: SpRows) -> object | None:
    if not rows:
        return None
    return next(iter(rows[0].values()))
