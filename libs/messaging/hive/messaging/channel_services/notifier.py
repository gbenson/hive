from .channel_service import ChannelService


class Notifier(ChannelService):
    outbound_queue = "matrix.message.send.requests"

    def tell_user(self, message: str, format: str = "text"):
        self.channel.send_to_queue(self.outbound_queue, {
            "format": format,
            "messages": [message],
        })
