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

    def _channel(self, **kwargs) -> Channel:
        name = kwargs.pop("name", "")
        return Channel(self._pika.channel(**kwargs), name=name)

    def channel(self, **kwargs) -> Channel:
        """Like :class:pika.channel.Channel` but with different defaults.

        :param name: Used by `Channel.consume_events()` to construct
             unique queue names.  May be required when more than one
             consumer with the same `Channel.consumer_name` may exist,
             which can happen if processes have multiple channels or
             if multiple processes share the same name.
        :param confirm_delivery: Whether to enable delivery confirmations.
            Hive's default is True.  Use `confirm_delivery=False` for the
            original Pika behaviour.
        """
        confirm_delivery = kwargs.pop("confirm_delivery", True)
        channel = self._channel(**kwargs)
        if confirm_delivery:
            channel.confirm_delivery()  # Don't fail silently.
        if self.on_channel_open:
            self.on_channel_open(channel)
        return channel
