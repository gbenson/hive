from .channel import Channel
from .wrapper import WrappedPikaThing


class Connection(WrappedPikaThing):
    def __init__(self, *args, **kwargs):
        self.on_channel_open = kwargs.pop("on_channel_open", None)
        super().__init__(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self._pika.is_open:
            self._pika.close()

    def _channel(self, *args, **kwargs) -> Channel:
        return Channel(self._pika.channel(*args, **kwargs))

    def channel(self, *args, **kwargs) -> Channel:
        """Like :class:pika.channel.Channel` but with different defaults.

        :param confirm_delivery: Whether to enable delivery confirmations.
            Hive's default is True.  Use `confirm_delivery=False` for the
            original Pika behaviour.
        """
        confirm_delivery = kwargs.pop("confirm_delivery", True)
        channel = self._channel(*args, **kwargs)
        if confirm_delivery:
            channel.confirm_delivery()  # Don't fail silently.
        if self.on_channel_open:
            self.on_channel_open(channel)
        return channel
