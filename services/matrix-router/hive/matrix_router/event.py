from datetime import datetime
from functools import cached_property
from typing import Any, Optional

from hive.chat.matrix import ClientEvent, EventContent


class MatrixEvent:
    """A decorated `ClientEvent`, as emitted by Matrix Commander.
    """
    def __init__(self, serialized: dict[str, Any]):
        self._decorated_event = serialized

    def json(self) -> dict[str, Any]:
        return self._decorated_event

    @cached_property
    def source(self) -> ClientEvent:
        """The raw event, as reported by Matrix Commander.
        """
        return ClientEvent(self._decorated_event["source"])

    @cached_property
    def event_type(self) -> str:
        """The type of the event, e.g. "m.room.message".
        """
        return self.source.event_type

    @cached_property
    def event_id(self) -> str:
        """The globally unique identifier for this event.
        """
        return self.source.event_id

    @cached_property
    def sender(self) -> str:
        """The sender of this event.
        """
        return self.source.sender

    @cached_property
    def timestamp(self) -> datetime:
        """Timestamp on originating homeserver when this event was sent.
        """
        return self.source.timestamp

    @cached_property
    def room_id(self) -> str:
        """The ID of the room associated with this event.
        """
        return self.source.room_id

    @cached_property
    def content(self) -> EventContent:
        """The body of this event, as created by the client which sent it.
        """
        return self.source.content

    @cached_property
    def body(self) -> str:
        """The textual representation of this message.
        """
        return self.content.body

    @cached_property
    def html(self) -> Optional[str]:
        """The HTML representation of this message.
        """
        if self.content.format != "org.matrix.custom.html":
            return None
        return self.content.formatted_body
