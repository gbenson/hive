import logging
import threading
import time

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from hive.common.functools import once
from hive.common.units import MINUTE, SECOND
from hive.config import read as read_config
from hive.messaging import (
    Channel,
    Connection,
    UnroutableError,
    blocking_connection,
)
from hive.service import RestartMonitor

from . import imap

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


class PublisherCallback:
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._event = threading.Event()
        self._result = None
        self._exception = None

    def __call__(self):
        d("Entering callback")
        try:
            self._result = self._func(*self._args, **self._kwargs)
        except Exception as exc:
            self._exception = exc
        finally:
            self._event.set()
            del self._func, self._args, self._kwargs
            d("Leaving callback")

    def join(self, *args, **kwargs):
        d("Waiting for callback")
        self._event.wait(*args, **kwargs)
        d("Callback returned")
        try:
            if self._exception:
                raise self._exception
            return self._result
        finally:
            del self._result, self._exception


class Publisher(threading.Thread):
    def __init__(self, conn: Connection):
        super().__init__(
            name="Publisher",
            daemon=True,
        )
        self.conn = conn
        self.channel = None
        self.is_running = False

    def start(self):
        d("Starting publisher thread")
        self.is_running = True
        super().start()

    def run(self):
        d("Publisher thread started")
        self.channel = self.conn.channel()
        while self.is_running:
            self.conn.process_data_events(time_limit=1 * SECOND)
        d("Publisher thread stopping")

    def publish_event(self, **kwargs):
        callback = PublisherCallback(self.channel.publish_event, **kwargs)
        self.conn.add_callback_threadsafe(callback)
        callback.join()

    def stop(self):
        d("Stopping publisher")
        self.is_running = False
        self.join()
        d("Publisher thread stopped")

        # Wait until all the data events have been processed
        self.conn.process_data_events(time_limit=1 * SECOND)
        d("Publisher stopped")


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
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            publisher = Publisher(conn)
            publisher.start()
            try:
                self._run(publisher)
            finally:
                publisher.stop()

    def _run(self, publisher: Publisher):
        with self._imap.connect() as imap:
            self._main_loop(publisher, imap)

    def _main_loop(self, publisher: Publisher, imap: imap.ClientConnection):
        logger.info("Polling")
        while True:
            start_time = datetime.now()
            count = self._process_messages(publisher, imap)
            elapsed = (datetime.now() - start_time).total_seconds()
            log = logger.info if count else logger.debug
            log("Processed %s messages in %.4f seconds", count, elapsed)
            sleep_time = self.cycle_time - elapsed
            if sleep_time <= 0:
                continue
            logger.debug("Sleeping for %.4f seconds", sleep_time)
            time.sleep(sleep_time)

    def _process_messages(
            self,
            publisher: Publisher,
            imap: imap.ClientConnection,
    ):
        num_processed = 0
        for mailbox_name in self._reading_lists:
            with imap.select(mailbox_name) as mailbox:
                for msg in mailbox.messages:
                    if not self._process_message(publisher, msg):
                        continue
                    num_processed += 1
        return num_processed

    def _process_message(self, publisher: Publisher, email: imap.Message):
        for header in ("To", "Cc", "Bcc"):
            if email[header]:
                d("Message %s has '%s:' header", email.uid, header)
                return False

        try:
            publisher.publish_event(
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
