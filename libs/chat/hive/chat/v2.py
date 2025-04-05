import os
import sys

from datetime import timedelta
from typing import Any, Literal, Optional
from uuid import uuid4

from cloudevents.pydantic import CloudEvent

from hive.common import utc_now
from hive.messaging import Channel

from .util import publish


def send_text(
        text: str,
        *,
        channel: Optional[Channel] = None,
) -> None:
    """https://pkg.go.dev/maunium.net/go/mautrix#Client.SendText
    """
    _publish(channel, "send_text", {"text": text})


def send_reaction(
        reaction: str,
        *,
        in_reply_to: str | CloudEvent,
        channel: Optional[Channel] = None,
) -> None:
    """https://pkg.go.dev/maunium.net/go/mautrix#Client.SendReaction
    """
    if isinstance(in_reply_to, CloudEvent):
        in_reply_to = in_reply_to.id
    _publish(channel, "send_reaction", {
        "event_id": in_reply_to,
        "reaction": reaction,
    })


def user_typing(
        timeout: timedelta | Literal[False],
        *,
        channel: Optional[Channel] = None,
) -> None:
    """https://pkg.go.dev/maunium.net/go/mautrix#Client.UserTyping
    """
    timeout = round(timeout.total_seconds() * 1e9) if timeout else 0
    _publish(channel, "user_typing", {"timeout": timeout})


try:
    SERVICE_NAME = os.path.basename(sys.argv[0])
except Exception:
    SERVICE_NAME = "unknown-service"


def _publish(
        channel: Optional[Channel],
        event_type: str,
        data: dict[str, Any],
) -> None:
    event_type = f"matrix_{event_type}_request"
    routing_key = f"{event_type.replace('_', '.')}s"
    event_type = f"net.gbenson.hive.{event_type}"
    message = CloudEvent(
        id=str(uuid4()),
        source=f"https://gbenson.net/hive/services/{SERVICE_NAME}",
        type=event_type,
        time=utc_now(),
        data=data,
    )
    publish(message, channel=channel, routing_key=routing_key)
