from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from hive.messaging import Channel

from ..imap import ClientConnection as IMAPConn


@dataclass
class Processor(ABC):
    mailboxes: Sequence[str]
    queue_name: str

    @abstractmethod
    def process_messages(self, channel: Channel, imap: IMAPConn) -> int:
        """Process messages from the specified mailboxes.
        Return the number of messages processed."""
        raise NotImplementedError
