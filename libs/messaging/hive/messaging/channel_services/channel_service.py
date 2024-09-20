from __future__ import annotations

import weakref

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..channel import Channel


class ChannelService:
    def __init__(self, channel: Channel):
        self.channel = weakref.proxy(channel)

    def _declared_queue(self, queue, **kwargs) -> str:
        """Declare a queue, returning its name.

        Intended to be wrapped in a cached_property.
        """
        self.channel.queue_declare(queue, **kwargs)
        return queue
