import logging

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from hive.messaging import Channel, UnroutableError

from .imap import ClientConnection as IMAPConn, Message

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Processor(ABC):
    mailboxes: Sequence[str]
    queue_name: str

    @abstractmethod
    def process_messages(self, channel: Channel, imap: IMAPConn) -> int:
        """Process messages from the specified mailboxes.
        Return the number of messages processed."""
        raise NotImplementedError


@dataclass
class ReadingListProcessor(Processor):
    queue_name: str = "readinglist.emails.received"

    def process_messages(self, channel: Channel, imap: IMAPConn) -> int:
        num_processed = 0
        for mailbox_name in self.mailboxes:
            with imap.select(mailbox_name) as mailbox:
                for msg in mailbox.messages:
                    if not self._process_message(channel, msg):
                        continue
                    num_processed += 1
        return num_processed

    def _process_message(self, channel: Channel, email: Message):
        for header in ("To", "Cc", "Bcc"):
            if email[header]:
                d("Message %s has '%s:' header", email.uid, header)
                return False

        try:
            channel.publish_event(
                message=bytes(email),
                content_type="message/rfc822",
                routing_key=self.queue_name,
                mandatory=True,
            )
        except UnroutableError:
            logger.info("Retaining message %s on %s", email.uid, email.server)
            return False

        d("Message %s queued", email.uid)
        email.delete()
        d("Message %s marked for deletion", email.uid)
        return True
