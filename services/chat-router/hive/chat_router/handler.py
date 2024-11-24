from abc import ABC, abstractmethod

from hive.chat import ChatMessage
from hive.messaging import Channel


class Handler(ABC):
    @property
    def priority(self) -> int:
        return 50

    @abstractmethod
    def handle(self, channel: Channel, message: ChatMessage) -> bool:
        """Handle `message`.

        :return: True if `message` was handled, otherwise False.
        """
        raise NotImplementedError  # pragma: no cover
