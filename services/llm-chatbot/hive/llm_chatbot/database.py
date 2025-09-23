from typing import Annotated, Any, Literal, TypeAlias, TypeVar

from pydantic import UUID4, StringConstraints

from valkey import Valkey
from valkey.exceptions import ResponseError, TimeoutError
from valkey.typing import ResponseT

from hive.common import dynamic_cast

T = TypeVar("T", bound="Database")

# The ID of an entry in a Redis/Valkey stream.  Both parts are 64-bit
# integers, the first part being the database server's Unix timestamp
# in milliseconds, and the second part being a sequence number used to
# distinguish IDs generated in the same millisecond.
StreamID: TypeAlias = Annotated[str, StringConstraints(pattern=r"^\d+-\d+$")]

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

    def xgroup_create(
            self,
            *args: Any,
            exist_ok: bool = True,
            **kwargs: Any,
    ) -> ResponseT:
        try:
            return super().xgroup_create(*args, **kwargs)
        except ResponseError as e:
            if exist_ok and "BUSYGROUP" in str(e):
                return True
            raise

    def xreadgroup(self, *args: Any, **kwargs: Any) -> ResponseT:
        try:
            return super().xreadgroup(*args, **kwargs)
        except TimeoutError as e:
            if str(e) == "Timeout reading from socket":
                return []
            raise
