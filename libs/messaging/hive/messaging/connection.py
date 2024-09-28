import logging

from threading import Event, Thread

from hive.common.units import SECOND

from .channel import Channel, PublisherChannel
from .wrapper import WrappedPikaThing

logger = logging.getLogger(__name__)
d = logger.debug


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


class PublisherConnection(Connection, Thread):
    def __init__(self, *args, **kwargs):
        thread_name = kwargs.pop("thread_name", "Publisher")
        Thread.__init__(self, name=thread_name, daemon=True)
        Connection.__init__(self, *args, **kwargs)
        self.is_running = True

    def __enter__(self):
        logger.info("Starting publisher thread")
        Thread.start(self)
        return Connection.__enter__(self)

    def run(self):
        logger.info("%s: thread started", self.name)
        while self.is_running:
            self.process_data_events(time_limit=1 * SECOND)
        logger.info("%s: thread stopping", self.name)
        self.process_data_events(time_limit=1 * SECOND)
        logger.info("%s: thread stopped", self.name)

    def __exit__(self, *exc_info):
        logger.info("Stopping publisher thread")
        self.is_running = False
        self.join()
        logger.info("Publisher thread stopped")
        return Connection.__exit__(self, *exc_info)

    def _channel(self, *args, **kwargs) -> Channel:
        return PublisherChannel(
            self._invoke,
            self._invoke(super()._channel, *args, **kwargs),
        )

    def _invoke(self, func, *args, **kwargs):
        callback = PublisherCallback(func, args, kwargs)
        self.add_callback_threadsafe(callback)
        return callback.join()


class PublisherCallback:
    def __init__(self, func, args, kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._event = Event()
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
