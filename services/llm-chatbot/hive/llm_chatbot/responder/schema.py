from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from hive.common import dynamic_cast

from ..database import ContextID, MessageID, StreamID, Role


class Message(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: MessageID
    time: datetime
    role: Role

    @property
    def text(self) -> str:
        extra_fields = self.model_extra
        if not extra_fields:
            return ""
        return dynamic_cast(str, extra_fields["content.text"])


class Request(BaseModel):
    """An entry in the requests stream.
    """
    id: StreamID
    """This request's entry ID in the requests stream."""

    type: str = Field(alias="action")
    context_id: ContextID
    message_id: MessageID
    time: datetime
