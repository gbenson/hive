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
    update_request_queue: str = "readinglist.update.requests"  # input
    update_event_routing_key: str = "readinglist.updates"      # output
    on_channel_open: Optional[Callable[[Channel], None]] = None

    @cached_property
    def wiki(self):
        return HiveWiki()

    def on_update_request(
        self,
        channel: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        entry = ReadingListEntry.from_email_summary_bytes(body)
        wikitext = entry.as_wikitext()
        self.wiki.page("Reading list").append(f"* {wikitext}")
        try:
            channel.publish_event(
                message=body,
                content_type=content_type,
                routing_key=self.update_event_routing_key,
            )
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

    def run(self):
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            channel.consume_requests(
                queue=self.update_request_queue,
                on_message_callback=self.on_update_request,
            )
            channel.start_consuming()
