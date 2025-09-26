import logging

from dataclasses import dataclass, field
from threading import Event, Thread
from typing import Any, Protocol, cast
from typing_extensions import Self

from hive.common.typing import AnyCallable
from hive.common.units import SECOND

from .channel import Channel
from .connection import Connection

logger = logging.getLogger(__name__)
d = logger.debug


class Invoker(Protocol):
    def __call__(
            self,
            func: AnyCallable,
            *args: Any,
            **kwargs: Any
    ) -> Any: ...


class PublisherConnection(Connection, Thread):
    def __init__(self, *args: Any, **kwargs: Any):
        thread_name = kwargs.pop("thread_name", "Publisher")
        poll_interval = kwargs.pop("poll_interval", 1 * SECOND)
        self._poll_interval = poll_interval.total_seconds()
        Thread.__init__(self, name=thread_name, daemon=True)
        Connection.__init__(self, *args, **kwargs)
        self.is_running = True

    def __enter__(self) -> Self:
        logger.info("Starting publisher thread")
        Thread.start(self)
        return Connection.__enter__(self)

    def run(self) -> None:
        logger.info("%s: thread started", self.name)
        while self.is_running:
            self._pika.process_data_events(time_limit=self._poll_interval)
        logger.info("%s: thread stopping", self.name)
        self._pika.process_data_events(time_limit=self._poll_interval)
        logger.info("%s: thread stopped", self.name)

    def __exit__(self, *exc_info: Any) -> None:
        logger.info("Stopping publisher thread")
        self.is_running = False
        self.join()
        logger.info("Publisher thread stopped")
        return Connection.__exit__(self, *exc_info)

    def _channel(self, *args: Any, **kwargs: Any) -> Channel:
        return cast(Channel, PublisherChannel(
            self._invoke,
            self._invoke(super()._channel, *args, **kwargs),
        ))

    def _invoke(self, func: AnyCallable, *args: Any, **kwargs: Any) -> Any:
        callback = PublisherCallback(func, args, kwargs)
        self._pika.add_callback_threadsafe(callback)
        return callback.join()


@dataclass
class PublisherCallback:
    _func: AnyCallable
    _args: tuple[str]
    _kwargs: dict[str, Any]
    _event: Event = field(default_factory=Event)
    _result: Any = None
    _exception: Exception | None = None

    def __call__(self) -> None:
        d("Entering callback")
        try:
            self._result = self._func(*self._args, **self._kwargs)
        except Exception as exc:
            self._exception = exc
        finally:
            self._event.set()
            del self._func, self._args, self._kwargs
            d("Leaving callback")

    def join(self, *args: Any, **kwargs: Any) -> Any:
        d("Waiting for callback")
        self._event.wait(*args, **kwargs)
        d("Callback returned")
        try:
            if self._exception:
                raise self._exception
            return self._result
        finally:
            del self._result, self._exception


@dataclass
class PublisherChannel:
    _invoker: Invoker
    _channel: Channel

    def __getattr__(self, attr: str) -> Any:
        result = getattr(self._channel, attr)
        if not callable(result):
            return result
        return PublisherInvoker(self._invoker, result)


@dataclass
class PublisherInvoker:
    _invoke: Invoker
    _func: AnyCallable

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._invoke(self._func, *args, **kwargs)
