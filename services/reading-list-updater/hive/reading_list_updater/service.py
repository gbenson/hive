import logging

from dataclasses import dataclass
from typing import Callable, Optional

from pika import BasicProperties
from pika.spec import Basic

from hive.messaging import Channel, blocking_connection

from .entry import ReadingListEntry

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


@dataclass
class Service:
    email_queue: str = "readinglist.emails.received"
    updates_queue: str = "readinglist.update.requests"
    on_channel_open: Optional[Callable[[Channel], None]] = None

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
            routing_key=self.updates_queue,
        )

    def run(self):
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            channel.consume_events(
                queue=self.email_queue,
                on_message_callback=self.on_email_received,
                dead_letter=True,
            )
            channel.start_consuming()
