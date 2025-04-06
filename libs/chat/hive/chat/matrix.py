from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel


class ClientEvent(BaseModel):
    """`ClientEvent` -- The format used for events returned from a
    homeserver to a client via the Client- Server API, or sent to an
    Application Service via the Application Services API.

    https://spec.matrix.org/v1.12/client-server-api/#room-event-format
    """

    type: str
    """The type of the event."""

    content: dict[str, Any]
    """The body of this event, as created by the client which sent it."""

    room_id: str
    """The ID of the room associated with this event."""

    event_id: str
    """The globally unique identifier for this event."""

    sender: str
    """The fully-qualified ID of the user who sent this event."""

    origin_server_ts: int
    """Timestamp (in milliseconds since the unix epoch) on originating
    homeserver when this event was sent."""

    @property
    def time(self) -> datetime:
        """The timestamp on the originating homeserver when this
        event was sent.
        """
        return datetime.fromtimestamp(
            self.origin_server_ts / 1000,
            tz=timezone.utc,
        )


class RoomMessageEvent(ClientEvent):
    """Event used when sending messages in a room.

    Messages are not limited to be text. The `msgtype` key outlines
    the type of message, e.g. text, audio, image, video, etc. The
    `body` key is text and MUST be used with every kind of `msgtype`
    as a fallback mechanism for when a client cannot render a
    message. This allows clients to display something even if it is
    just plain text.

    https://spec.matrix.org/v1.12/client-server-api/#mroommessage
    """

    type: Literal["m.room.message"]
    """The type of the event."""

    content: RoomMessageEventContent
    """The body of this event, as created by the client which sent it."""


class RoomMessageEventContent(BaseModel):
    msgtype: str
    """The type of the message, e.g. "m.text", "m.image"."""

    body: str
    """The textual representation of this message."""
