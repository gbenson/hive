from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class AnyCallable(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def dynamic_cast(typ: type[T], val: Any) -> T:
    """Cast a value to a type, with checking at runtime.

    :returns: The value, unchanged, if it conforms to the specified type,
    :raises TypeError: if the value does not conform to the specified type.
    """
    if isinstance(val, typ):
        return val
    raise TypeError(val.__class__.__name__)
