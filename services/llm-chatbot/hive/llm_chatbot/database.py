from typing import Any, Literal, TypeAlias, TypeVar

from pydantic import UUID4
from valkey import Valkey

from hive.common import dynamic_cast

T = TypeVar("T", bound="Database")


ContextID: TypeAlias = UUID4
MessageID: TypeAlias = UUID4
Role: TypeAlias = Literal["hive", "user"]


class Database(Valkey):
    @classmethod
    def connect(
            cls: type[T],
            url: str = "valkey://valkey",
            *,
            decode_responses: bool = True,
            **kwargs: Any
    ) -> T:
        client = cls.from_url(url, decode_responses=True, **kwargs)
        return dynamic_cast(cls, client)


__all__ = [
    "ContextID",
    "Database",
    "MessageID",
    "Role",
]
