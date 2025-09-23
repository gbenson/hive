import json

from datetime import datetime
from typing import Any, Literal, TypeVar

from cloudevents.pydantic import CloudEvent
from pydantic import BaseModel

from hive.common import dynamic_cast

from ..database import ContextID, MessageID, Role
from .dictutils import flatten, update_noreplace

T = TypeVar("T", bound="BaseRequest")


class Message(BaseModel):
    id: MessageID
    role: Role
    content: dict[str, Any]


class BaseRequest(BaseModel):
    """Base class for "net.gbenson.hive.llm_chatbot_*_request" CloudEvents.
    """
    context_id: ContextID
    time: datetime

    @classmethod
    def from_cloudevent(cls: type[T], event: CloudEvent) -> T:
        values = dynamic_cast(dict, event.data)
        update_noreplace(values, time=event.time)
        return cls.model_validate(values)

    def as_key_value_pairs(self) -> dict[str, Any]:
        values = json.loads(self.model_dump_json())
        if (time := values["time"]).endswith("000Z"):
            values["time"] = time[:-4] + "Z"
        return flatten(values)


class MessageRequest(BaseRequest):
    message: Message

    def as_key_value_pairs(self) -> dict[str, Any]:
        values = super().as_key_value_pairs()
        values = {
            self._fixup_key(key): value
            for key, value in values.items()
            if key != "message.content.type"
        }
        return values

    @classmethod
    def _fixup_key(cls, key: str) -> str:
        if key == "message.id":
            return "message_id"
        if key == "message.role":
            return "role"
        if key.startswith("message.content."):
            return key.replace("message.content.", "content.", 1)
        return key


class GenerateResponseRequest(BaseRequest):
    action: Literal["generate_response"] = "generate_response"
    message_id: MessageID


class UpdateContextRequest(MessageRequest):
    action: Literal["upsert_message"] = "upsert_message"
