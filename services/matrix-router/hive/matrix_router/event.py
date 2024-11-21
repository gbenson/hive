from __future__ import annotations

from datetime import datetime, timezone
from functools import cached_property
from typing import Any, Optional


class MatrixEvent:
    """A decorated `ClientEvent`, as emitted by Matrix Commander.
    """
    def __init__(self, serialized: dict[str, Any]):
        self._decorated_event = serialized

    def json(self) -> dict[str, Any]:
        return self._decorated_event

    @cached_property
    def _event(self) -> ClientEvent:
        """The undecorated event, as reported by Matrix Commander.
        """
        return ClientEvent(self._decorated_event["source"])

    @cached_property
    def event_type(self) -> str:
        """The type of the event, e.g. "m.room.message".
        """
        return self._event.event_type

    @cached_property
    def event_id(self) -> str:
        """The globally unique identifier for this event.
        """
        return self._decorated_event["event_id"]

    @cached_property
    def sender(self) -> str:
        """The sender of this event.
        """
        return self._decorated_event["sender"]

    @cached_property
    def timestamp(self) -> datetime:
        """Timestamp on originating homeserver when this event was sent.
        """
        return datetime.fromtimestamp(
            self.timestamp_ms / 1000,
            tz=timezone.utc,
        )

    @cached_property
    def timestamp_ms(self) -> datetime:
        """Timestamp (in milliseconds since the unix epoch) on
        originating homeserver when this event was sent.
        """
        return self._decorated_event["server_timestamp"]

    @cached_property
    def room_id(self) -> str:
        """The ID of the room associated with this event.
        """
        return self._decorated_event["room_id"]

    @cached_property
    def content(self) -> EventContent:
        """The body of this event, as created by the client which sent it.
        """
        return self._event.content

    @cached_property
    def body(self) -> str:
        """The textual representation of this message.
        """
        return self._decorated_event["body"]

    @cached_property
    def html(self) -> Optional[str]:
        """The HTMLrepresentation of this message.
        """
        if self._decorated_event.get("format") != "org.matrix.custom.html":
            return None
        return self._decorated_event["formatted_body"]


class ClientEvent:
    """An undecorated `ClientEvent`, as reported by Matrix Commander.

    **7.2 Room event format**

    `ClientEvent` -- The format used for events returned from a
        homeserver to a client via the Client- Server API, or sent
        to an Application Service via the Application Services API.

    https://spec.matrix.org/v1.12/client-server-api/#room-event-format
    """
    def __init__(self, serialized: dict[str, Any]):
        self._event = serialized

    @cached_property
    def event_type(self) -> str:
        """The type of the event, e.g. "m.room.message".
        """
        return self._event["type"]

    @cached_property
    def content(self) -> EventContent:
        """The body of this event, as created by the client which sent it.
        """
        return EventContent(self._event["content"])


class EventContent:
    """The content of an "m.room.message" event.
    """
    def __init__(self, serialized: dict[str, Any]):
        self._content = serialized

    @cached_property
    def msgtype(self) -> str:
        """The type of the message, e.g. "m.text", "m.image".
        """
        return self._content["msgtype"]
