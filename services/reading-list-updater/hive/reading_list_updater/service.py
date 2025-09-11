import logging

from datetime import datetime
from email.utils import format_datetime
from functools import cached_property
from typing import Any, Optional

from hive.common import blake2b_digest_uuid, httpx
from hive.mediawiki import HiveWiki
from hive.messaging import Channel, Message
from hive.service import HiveService

from .decoration import maybe_decorate_entry
from .entry import ReadingListEntry
from .opengraph import opengraph_properties

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


class Service(HiveService):
    update_request_queue: str = "readinglist.update.requests"  # input
    fetched_sources_routing_key: str = "readinglist.shares"

    @cached_property
    def wiki(self):
        return HiveWiki()

    def on_update_request(self, channel: Channel, message: Message):
        event_time: Optional[datetime] = None

        if message.is_cloudevent:
            event = message.event()
            email_summary = event.data
            event_time = event.time
            email_summary["date"] = format_datetime(event_time)
        else:
            email_summary = message.json()

        d("Update request: %r", email_summary)
        entry = ReadingListEntry.from_email_summary(email_summary)

        if event_time:
            self.maybe_update_llm_context(
                channel,
                (undecorated_json := entry.json()),
                time=event_time,
            )

        try:
            self.maybe_decorate_entry(channel, entry)
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

        if event_time:
            if (decorated_json := entry.json()) != undecorated_json:
                self.maybe_update_llm_context(
                    channel,
                    decorated_json,
                    time=event_time,
                )

        wikitext = entry.as_wikitext()
        self.wiki.page("Reading list").append(f"* {wikitext}")

        try:
            self.maybe_acknowledge(channel, entry)
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

    def maybe_update_llm_context(self, *args: Any, **kwargs: Any) -> None:
        try:
            self._maybe_update_llm_context(*args, **kwargs)
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

    def _maybe_update_llm_context(
            self,
            channel: Channel,
            entry: dict[str, Any],
            *,
            time: datetime,
    ) -> None:
        if not (source := entry.pop("source", None)):
            return  # not from a matrix event
        if source.get("type") != "net.gbenson.hive.matrix_event":
            return  # ditto
        del entry["timestamp"]

        channel.publish_request(
            routing_key="llm.chatbot.requests",
            type="net.gbenson.hive.llm_chatbot_update_context_request",
            time=time,
            data={
                "context_id": str(blake2b_digest_uuid(source["room_id"])),
                "message": {
                    "id": str(blake2b_digest_uuid(source["event_id"])),
                    "role": "user",
                    "content": {
                        "type": "reading_list_update",
                        "reading_list_update": entry,
                    },
                },
            },
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

    def maybe_acknowledge(
            self,
            channel: Channel,
            entry: ReadingListEntry,
    ) -> None:
        if not (event_id := entry.source_matrix_event_id):
            return
        channel.send_reaction("👍", in_reply_to=event_id)
        channel.set_user_typing(False)

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_requests(
                queue=self.update_request_queue,
                on_message_callback=self.on_update_request,
            )
            channel.start_consuming()
