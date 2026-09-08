from collections.abc import Iterator
from typing import TypeVar

T = TypeVar("T")


def iter_batches(items: list[T], batch_size: int) -> Iterator[list[T]]:
    """Yield consecutive slices (legacy PHP sends Kcell batches of 200 messages)."""
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]
