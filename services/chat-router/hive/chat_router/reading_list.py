import logging

from email.utils import format_datetime
from urllib.parse import urlparse

from cloudevents.abstract import CloudEvent
from cloudevents.conversion import to_dict

from hive.chat import set_user_typing
from hive.common.units import SECOND
from hive.messaging import Channel

logger = logging.getLogger(__name__)
d = logger.info


def handle_link(channel: Channel, candidate: str, event: CloudEvent) -> bool:
    try:
        url = urlparse(candidate.split(maxsplit=1)[0])
    except Exception:
        return False
    if url.scheme not in {"http", "https"}:
        return False

    d("Reading list update: %r", candidate)
    set_user_typing(5 * SECOND)
    request_reading_list_update(channel, candidate, event)

    return True


def request_reading_list_update(
        channel: Channel,
        unparsed_user_input: str,
        event: CloudEvent,
) -> None:
    channel.publish_request(
        message={
            "meta": {
                "origin": {
                    "channel": "matrix",
                    "message": to_dict(event),
                },
            },
            "date": format_datetime(event.time),
            "body": unparsed_user_input,
        },
        routing_key="readinglist.update.requests",
    )
