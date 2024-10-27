from email.utils import format_datetime
from urllib.parse import urlparse

from hive.messaging import Channel

from .event import MatrixEvent


def is_reading_list_update(event: MatrixEvent) -> bool:
    if event.event_type != "m.room.message":
        return False
    if event.content.msgtype != "m.text":
        return False
    try:
        url = urlparse(event.body.split(maxsplit=1)[0])
    except Exception:
        return False
    return url.scheme in {"http", "https"}


def route_reading_list_update(channel: Channel, event: MatrixEvent):
    assert is_reading_list_update(event)

    channel.publish_request(
        message={
            "origin": {
                "channel": "matrix",
                "room_id": event.room_id,
                "event_id": event.event_id,
            },
            "date": format_datetime(event.timestamp),
            "body": event.body,
        },
        routing_key="readinglist.update.requests",
        mandatory=True,
    )
