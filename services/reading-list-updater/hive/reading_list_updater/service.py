import logging

from dataclasses import dataclass
from functools import cached_property

from hive.common import httpx
from hive.mediawiki import HiveWiki
from hive.messaging import Channel, Message
from hive.service import HiveService

from .decoration import maybe_decorate_entry
from .entry import ReadingListEntry
from .opengraph import opengraph_properties

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


@dataclass
class Service(HiveService):
    update_request_queue: str = "readinglist.update.requests"  # input
    update_event_routing_key: str = "readinglist.updates"      # output
    fetched_sources_routing_key: str = "readinglist.shares"

    @cached_property
    def wiki(self):
        return HiveWiki()

    def on_update_request(self, channel: Channel, message: Message):
        email_summary = message.json()
        d("Update request: %r", email_summary)
        entry = ReadingListEntry.from_email_summary(email_summary)
        try:
            self.maybe_decorate_entry(channel, entry)
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

        wikitext = entry.as_wikitext()
        self.wiki.page("Reading list").append(f"* {wikitext}")

        meta = email_summary.get("meta", {})
        if not meta:
            email_summary["meta"] = meta
        meta["reading_list_entry"] = entry.json()
        channel.maybe_publish_event(
            message=email_summary,
            routing_key=self.update_event_routing_key,
        )

    def maybe_decorate_entry(
            self,
            channel: Channel,
            entry: ReadingListEntry,
    ):
        r = httpx.get(entry.url)
        r.raise_for_status()

        if not r.extensions.get("from_cache"):
            channel.maybe_publish_event(
                message={
                    "request_url": str(entry.url),
                    **httpx.response_as_json(r),
                },
                routing_key=self.fetched_sources_routing_key,
            )

        maybe_decorate_entry(entry, opengraph_properties(r.text))

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_requests(
                queue=self.update_request_queue,
                on_message_callback=self.on_update_request,
            )
            channel.start_consuming()
