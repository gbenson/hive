import logging

from dataclasses import dataclass
from functools import cached_property

from hive.mediawiki import HiveWiki
from hive.messaging import Channel, Message
from hive.service import HiveService

from .decoration import maybe_decorate_entry
from .entry import ReadingListEntry

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


@dataclass
class Service(HiveService):
    update_request_queue: str = "readinglist.update.requests"  # input
    update_event_routing_key: str = "readinglist.updates"      # output

    @cached_property
    def wiki(self):
        return HiveWiki()

    def on_update_request(self, channel: Channel, message: Message):
        email_summary = message.json()
        d("Update request: %r", email_summary)
        entry = ReadingListEntry.from_email_summary(email_summary)
        maybe_decorate_entry(entry)
        wikitext = entry.as_wikitext()
        self.wiki.page("Reading list").append(f"* {wikitext}")
        try:
            channel.publish_event(
                message=email_summary,
                routing_key=self.update_event_routing_key,
            )
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_requests(
                queue=self.update_request_queue,
                on_message_callback=self.on_update_request,
            )
            channel.start_consuming()
