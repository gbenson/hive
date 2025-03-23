import logging

from threading import Event, Thread

from hive.common.units import SECOND

from .channel import Channel
from .connection import Connection

logger = logging.getLogger(__name__)
d = logger.debug


class PublisherConnection(Connection, Thread):
    def __init__(self, *args, **kwargs):
        thread_name = kwargs.pop("thread_name", "Publisher")
        poll_interval = kwargs.pop("poll_interval", 1 * SECOND)
        self._poll_interval = poll_interval.total_seconds()
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
            self.process_data_events(time_limit=self._poll_interval)
        logger.info("%s: thread stopping", self.name)
        self.process_data_events(time_limit=self._poll_interval)
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


class PublisherChannel:
    def __init__(self, invoker, channel):
        self._invoker = invoker
        self._channel = channel

    def __getattr__(self, attr):
        result = getattr(self._channel, attr)
        if not callable(result):
            return result
        return PublisherInvoker(self._invoker, result)


class PublisherInvoker:
    def __init__(self, invoker, func):
        self._invoke = invoker
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._invoke(self._func, *args, **kwargs)
