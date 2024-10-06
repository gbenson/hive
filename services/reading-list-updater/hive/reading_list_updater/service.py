import logging

from dataclasses import dataclass
from functools import cached_property
from typing import Callable, Optional

from pika import BasicProperties
from pika.spec import Basic

from hive.mediawiki import HiveWiki
from hive.messaging import Channel, blocking_connection

from .entry import ReadingListEntry

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


@dataclass
class Service:
    email_queue: str = "readinglist.emails.received"
    append_request_queue: str = "readinglist.append.requests"
    on_channel_open: Optional[Callable[[Channel], None]] = None

    @cached_property
    def wiki(self):
        return HiveWiki()

    def on_append_request(
        self,
        channel: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        entry = ReadingListEntry.from_json_bytes(body)
        wikitext = entry.as_wikitext()
        self.wiki.page("Reading list").append(f"* {wikitext}")

    def on_email_received(
        self,
        channel: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "message/rfc822":
            raise ValueError(content_type)
        entry = ReadingListEntry.from_email_bytes(body)
        channel.publish_request(
            message=entry.as_dict(),
            routing_key=self.append_request_queue,
        )

    def run(self):
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            channel.consume_events(
                queue=self.email_queue,
                on_message_callback=self.on_email_received,
                dead_letter=True,
            )
            channel.consume_requests(
                queue=self.append_request_queue,
                on_message_callback=self.on_append_request,
                dead_letter=True,
            )
            channel.start_consuming()
