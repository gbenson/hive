from datetime import datetime
from typing import Annotated, TypeAlias, TypeVar

from cloudevents.pydantic import CloudEvent
from pydantic import BaseModel, Field, StringConstraints

from hive.common import dynamic_cast
from hive.common.dictutil import update_noreplace

EventID: TypeAlias = Annotated[str, StringConstraints(pattern=r"^\$.+")]
RoomID: TypeAlias = Annotated[str, StringConstraints(pattern=r"^!.+")]

T = TypeVar("T", bound="Request")


class Source(BaseModel):
    event_id: EventID
    room_id: RoomID


class Request(BaseModel):
    time: datetime
    source: Source = Field(alias="created_from")
    user_input: str = Field(alias="command")

    @classmethod
    def from_cloudevent(cls: type[T], event: CloudEvent) -> T:
        values = dynamic_cast(dict, event.data)
        update_noreplace(values, time=event.time)
        return cls.model_validate(values)
