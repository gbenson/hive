from collections.abc import Iterator, Mapping
from typing import Any


def flatten_dict(
        src: Mapping[str, Any],
        sep: str = ".",
        prefix: str = "",
) -> Iterator[str, Any]:
    for key, value in src.items():
        if isinstance(value, str):
            yield f"{prefix}{key}", value
            continue
        if isinstance(value, Mapping):
            yield from flatten_dict(value, sep, f"{prefix}{key}{sep}")
            continue
        raise TypeError(type(value).__name__)
