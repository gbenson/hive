import json

from datetime import datetime
from typing import Any, Literal, TypeAlias, TypeVar

from cloudevents.abstract import CloudEvent
from pydantic import BaseModel, Field, UUID4

from .util import flatten_dict

T = TypeVar("T", bound="BaseRequest")

ContextID: TypeAlias = UUID4
MessageID: TypeAlias = UUID4
Role: TypeAlias = Literal["hive", "user"]


class BaseMessage(BaseModel):
    """A message that takes the timestamp of the request it was
    embedded within.  This is the format in which messages are
    transmitted over AMQP.
    """
    id: MessageID
    role: Role
    content: dict[str, Any]


class Message(BaseMessage):
    time: datetime

    def as_key_value_pairs(self) -> dict[str, Any]:
        src = json.loads(self.model_dump_json())
        return dict(flatten_dict(src))


class BaseRequest(BaseModel):
    context_id: ContextID
    time: datetime

    @classmethod
    def from_cloudevent(cls: type[T], event: CloudEvent) -> T:
        request = event.data.copy()
        if "time" in request:
            raise ValueError(request)  # pragma: no cover
        request["time"] = event.time
        return cls.model_validate(request)


class MessageRequest(BaseRequest):
    """A request with an embedded message as part of its payload.
    """
    embedded_message: BaseMessage = Field(alias="message")

    @property
    def message(self) -> Message:
        message = self.embedded_message.model_dump()
        if "time" in message:
            raise ValueError(message)  # pragma: no cover
        message["time"] = self.time
        return Message.model_validate(message)


class GenerateResponseRequest(BaseRequest):
    pass


class UpdateContextRequest(MessageRequest):
    pass
