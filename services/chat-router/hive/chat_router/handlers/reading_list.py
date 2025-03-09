import logging

from email.utils import format_datetime
from html import escape
from urllib.parse import urlparse

from hive.chat import ChatMessage, tell_user
from hive.messaging import Channel

from ..handler import Handler

logger = logging.getLogger(__name__)
d = logger.info


class ReadingListUpdateHandler(Handler):
    def handle(self, channel: Channel, message: ChatMessage) -> bool:
        first_two = message.text.split(maxsplit=1)[:2]
        if not first_two:
            return False
        raw_url = first_two.pop(0)
        if (is_no_share := (raw_url.lower() == "nosh")):
            if not first_two:
                return False
            raw_url = first_two.pop(0)

        try:
            url = urlparse(raw_url)
        except Exception:
            return False
        if url.scheme not in {"http", "https"}:
            return False
        if is_no_share:
            d("No share: %r", message.text)
            return True

        d("Reading list update: %r", message.text)
        self.request_reading_list_update(channel, message)

        try:
            self.update_message_in_webui(channel, message)
        except Exception:
            logger.warning(
                "EXCEPTION processing %s",
                message,
                exc_info=True,
            )

        return True

    def request_reading_list_update(
            self,
            channel: Channel,
            message: ChatMessage
    ):
        channel.publish_request(
            message={
                "meta": {
                    "origin": {
                        "channel": "chat",
                        "message": message.json(),
                    },
                },
                "date": format_datetime(message.timestamp),
                "body": message.text,
            },
            routing_key="readinglist.update.requests",
        )

    def update_message_in_webui(
            self,
            channel: Channel,
            message: ChatMessage
    ):
        if message.html:
            split_html = message.html.split(maxsplit=1)
        else:
            split_text = message.text.split(maxsplit=1)
            split_html = list(map(escape, split_text))

        link = split_html[0]
        if not link.startswith("http"):
            raise ValueError(link)
        if '"' in link:
            raise ValueError(link)
        split_html[0] = f'<a href="{link}">{link}</a>'

        message.html = " ".join(split_html)
        tell_user(message, channel=channel)
