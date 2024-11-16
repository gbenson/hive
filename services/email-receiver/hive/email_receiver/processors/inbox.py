import logging

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from valkey import Valkey

from hive.messaging import Channel, UnroutableError

from ..imap import ClientConnection as IMAPConn
from .processor import Processor

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class InboxProcessor(Processor):
    queue_name: str = "inbox.emails.received"
    valkey_url: str = "valkey://email-receiver-valkey"
    valkey_key: str = "message_ids"

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)

    def process_messages(self, channel: Channel, imap: IMAPConn) -> int:
        num_processed = 0

        now = str(datetime.now().timestamp()).encode()
        mark_seen_later = {}

        for mailbox_name in self.mailboxes:
            with imap.select(mailbox_name) as mailbox:
                messagerefs = list(mailbox.messages_by_id)
                message_ids = [r.message_id for r in messagerefs]

                for msgref, message_id, score in zip(
                        messagerefs,
                        message_ids,
                        self._valkey.zmscore(self.valkey_key, message_ids),
                ):
                    if score is not None:
                        mark_seen_later[message_id] = now
                        continue

                    if not (message_bytes := msgref.get_message_bytes()):
                        mark_seen_later[message_id] = now  # XXX?
                        continue

                    try:
                        channel.publish_event(
                            message=message_bytes,
                            content_type="message/rfc822",
                            routing_key=self.queue_name,
                            mandatory=True,
                        )
                        d("Message %s queued", message_id)

                    except UnroutableError:
                        continue

                    self._valkey.zadd(self.valkey_key, {message_id: now})
                    num_processed += 1

        if mark_seen_later:
            self._valkey.zadd(self.valkey_key, mark_seen_later)

        # XXX TODO: stop this growing forever
        # self._valkey.zremrangebyscore(self.valkey_key, "-inf", now - 1e-9)

        return num_processed
