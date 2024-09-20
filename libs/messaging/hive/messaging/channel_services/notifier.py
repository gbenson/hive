from functools import cached_property

from .channel_service import ChannelService


class Notifier(ChannelService):
    @cached_property
    def outbound_queue(self) -> str:
        return self._declared_queue(
            "matrix.messages.outgoing",
            durable=True,
        )

    def tell_user(self, message: str, format: str = "text"):
        self.channel.send_to_queue(self.outbound_queue, {
            "format": format,
            "messages": [message],
        })
