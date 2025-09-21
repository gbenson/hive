from collections.abc import Iterator, Mapping
from typing import Any


def flatten(
        src: Mapping[str, Any],
        *,
        sep: str = ".",
        prefix: str = "",
) -> dict[str, Any]:
    return dict(_flatten(src, sep, prefix))


def _flatten(
        src: Mapping[str, Any],
        sep: str,
        prefix: str,
) -> Iterator[tuple[str, Any]]:
    for key, value in src.items():
        if isinstance(value, str):
            yield f"{prefix}{key}", value
            continue
        if isinstance(value, Mapping):
            yield from _flatten(value, sep, f"{prefix}{key}{sep}")
            continue
        raise TypeError(type(value).__name__)


def update_noreplace(
        target: dict[str, Any],
        **source: Any,
) -> None:
    if (conflicts := set(source.keys()) & set(target.keys())):
        raise ValueError(", ".join(sorted(conflicts)))
    target.update(source)
