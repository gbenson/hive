import logging
import time

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from hive.common.functools import once
from hive.common.units import MINUTE
from hive.config import read as read_config
from hive.messaging import publisher_connection, Channel, UnroutableError
from hive.service import RestartMonitor

from . import imap

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Receiver:
    config_key: str = "email"
    queue_name: str = "readinglist.emails.received"
    cycle_time: float = 1 * MINUTE
    on_channel_open: Optional[Callable[[Channel], None]] = None

    def __post_init__(self):
        config = read_config(self.config_key)
        try:
            imap_config = config[self.config_key]["imap"]
            self._imap = imap.Client(imap_config)
            mbox_config = imap_config["mailboxes"]
            self._reading_lists = mbox_config["reading_lists"]

        except KeyError as e:
            raise RuntimeError("Service not configured") from e

    def run(self):
        with publisher_connection(
                on_channel_open=self.on_channel_open
        ) as conn:
            self._run(conn.channel())

    def _run(self, channel: Channel):
        with self._imap.connect() as imap:
            self._main_loop(channel, imap)

    def _main_loop(self, channel: Channel, imap: imap.ClientConnection):
        logger.info("Polling")
        while True:
            start_time = datetime.now()
            count = self._process_messages(channel, imap)
            elapsed = (datetime.now() - start_time).total_seconds()
            log = logger.info if count else logger.debug
            log("Processed %s messages in %.4f seconds", count, elapsed)
            sleep_time = self.cycle_time - elapsed
            if sleep_time <= 0:
                continue
            logger.debug("Sleeping for %.4f seconds", sleep_time)
            time.sleep(sleep_time)

    def _process_messages(self, channel: Channel, imap: imap.ClientConnection):
        num_processed = 0
        for mailbox_name in self._reading_lists:
            with imap.select(mailbox_name) as mailbox:
                for msg in mailbox.messages:
                    if not self._process_message(channel, msg):
                        continue
                    num_processed += 1
        return num_processed

    def _process_message(self, channel: Channel, email: imap.Message):
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


def main():
    logging.basicConfig(level=logging.INFO)
    rsm = RestartMonitor()
    receiver = Receiver(on_channel_open=once(rsm.report_via_channel))
    receiver.run()
