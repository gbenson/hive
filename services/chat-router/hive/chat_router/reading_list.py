import logging

from email.utils import format_datetime
from urllib.parse import urlparse

from cloudevents.abstract import CloudEvent
from cloudevents.conversion import to_dict

from hive.common.units import SECOND
from hive.messaging import Channel

logger = logging.getLogger(__name__)
d = logger.info


def startswith_link(s: str) -> bool:
    try:
        url = urlparse(s.split(maxsplit=1)[0])
    except Exception:
        return False
    return url.scheme in {"http", "https"}


def request_reading_list_update(
        channel: Channel,
        event: CloudEvent,
        user_input: str,
) -> None:
    d("Reading list update: %r", user_input)
    channel.set_user_typing(5 * SECOND)
    channel.publish_request(
        message={
            "meta": {
                "origin": {
                    "channel": "matrix",
                    "message": to_dict(event),
                },
            },
            "date": format_datetime(event.time),
            "body": user_input,
        },
        routing_key="readinglist.update.requests",
    )
