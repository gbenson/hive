import logging
import time

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from hive.common import read_config
from hive.common.units import MINUTE
from hive.messaging import Channel
from hive.service import HiveService

from . import imap
from .processors import Processor, DEFAULT_PROCESSORS

logger = logging.getLogger(__name__)


@dataclass
class Service(HiveService):
    config_key: str = "email"
    processors: Sequence[Processor] = field(default_factory=list)
    cycle_time: float = 1 * MINUTE

    def __post_init__(self):
        config = read_config(self.config_key)
        try:
            imap_config = config[self.config_key]["imap"]
            self._imap = imap.Client(imap_config)
            if self.processors:
                return
            mbox_config = imap_config["mailboxes"]
            for config_key, cls in DEFAULT_PROCESSORS.items():
                mailboxes = mbox_config.get(config_key)
                if not mailboxes:
                    continue
                self.processors.append(cls(mailboxes))
            if not self.processors:
                raise RuntimeError("Service not configured")

        except KeyError as e:
            raise RuntimeError("Service not configured") from e

    def run(self):
        with self.publisher_connection() as conn:
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

    def _process_messages(
            self,
            channel: Channel,
            imap: imap.ClientConnection,
    ) -> int:
        return sum(
            p.process_messages(channel, imap)
            for p in self.processors
        )
