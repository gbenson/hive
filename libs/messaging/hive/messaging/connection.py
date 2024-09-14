from .channel import Channel
from .wrapper import WrappedPikaThing


class Connection(WrappedPikaThing):
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self._pika.close()

    def channel(self, *args, **kwargs):
        """Like :class:pika.channel.Channel` but with different defaults.

        :param confirm_delivery: Whether to enable delivery confirmations.
            Hive's default is True.  Use `confirm_delivery=False` for the
            original Pika behaviour.
        """
        confirm_delivery = kwargs.pop("confirm_delivery", True)
        channel = Channel(self._pika.channel(*args, **kwargs))
        if confirm_delivery:
            channel.confirm_delivery()  # Don't fail silently.
        return channel
