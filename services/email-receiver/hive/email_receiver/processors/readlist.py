import logging

from dataclasses import dataclass

from hive.messaging import Channel, UnroutableError

from ..imap import ClientConnection as IMAPConn, Message
from .processor import Processor

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class ReadingListProcessor(Processor):
    queue_name: str = "readinglist.update.requests"

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
            channel.publish(
                message=email.summary,
                routing_key=self.queue_name,
            )
        except UnroutableError:
            logger.info("Retaining message %s on %s", email.uid, email.server)
            return False

        d("Message %s queued", email.uid)
        email.delete()
        d("Message %s marked for deletion", email.uid)
        return True
