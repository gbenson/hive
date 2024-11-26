from __future__ import annotations

from datetime import datetime, timezone
from functools import cached_property
from typing import Any, Optional


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

    def json(self):
        return self._event

    @cached_property
    def content(self) -> EventContent:
        """The body of this event, as created by the client which sent it.
        """
        return EventContent(self._event["content"])

    @cached_property
    def event_id(self) -> str:
        """The globally unique identifier for this event.
        """
        return self._event["event_id"]

    @cached_property
    def event_type(self) -> str:
        """The type of the event, e.g. "m.room.message".
        """
        return self._event["type"]

    @cached_property
    def room_id(self) -> str:
        """The ID of the room associated with this event.
        """
        return self._event["room_id"]

    @cached_property
    def sender(self) -> str:
        """The fully-qualified ID of the user who sent this event.
        """
        return self._event["sender"]

    @cached_property
    def timestamp(self) -> datetime:
        """The timestamp on the originating homeserver when this
        event was sent.
        """
        return datetime.fromtimestamp(
            self._event["origin_server_ts"] / 1000,
            tz=timezone.utc,
        )


class EventContent:
    """The content of an "m.room.message" event.

    https://spec.matrix.org/v1.12/client-server-api/#mtext
    """
    def __init__(self, serialized: dict[str, Any]):
        self._content = serialized

    @cached_property
    def msgtype(self) -> str:
        """The type of the message, e.g. "m.text", "m.image".
        """
        return self._content["msgtype"]

    @cached_property
    def body(self) -> str:
        """The body of the message.
        """
        return self._content["body"]

    @cached_property
    def format(self) -> Optional[str]:
        """The format used in the formatted_body.
        """
        return self._content.get("format")

    @cached_property
    def formatted_body(self) -> str:
        """The formatted version of the `body`.
        """
        return self._content["formatted_body"]
