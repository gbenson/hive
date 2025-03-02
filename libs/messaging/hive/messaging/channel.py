import json
import logging
import os
import sys

from deprecated import deprecated
from functools import cache, cached_property
from typing import Callable, Optional

from pika import BasicProperties, DeliveryMode

from . import semantics
from .message import Message
from .wrapper import WrappedPikaThing

logger = logging.getLogger(__name__)


class Channel(WrappedPikaThing):
    """The primary entry point for interacting with Hive's message bus.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pre_publish_hooks = []

    def publish(self, *, routing_key: str, **kwargs):
        semantics.publish_may_drop(kwargs)
        exchange = self._fanout_exchange_for(routing_key)
        return self._publish(exchange=exchange, **kwargs)

    def maybe_publish(self, **kwargs):
        try:
            return self.publish(**kwargs)
        except Exception:
            logger.warning("EXCEPTION", exc_info=True)

    def consume(
            self,
            *,
            queue: str,
            on_message_callback: Callable,
    ):
        exchange = self._fanout_exchange_for(queue)

        if (prefix := self.consumer_name):
            queue = f"{prefix}.{queue}"
        if (prefix := self.exclusive_queue_prefix):
            queue = f"{prefix}{queue}"

        self.queue_declare(
            queue,
            dead_letter_routing_key=queue,
            durable=True,
        )

        self.queue_bind(
            queue=queue,
            exchange=exchange,
        )

        return self._basic_consume(queue, on_message_callback)

    # QUEUES are declared by their consuming service

    # CONSUME_* methods process to completion or dead-letter the message

    # REQUESTS are things we're asking to be done:
    # - Each request queue has exactly one consuming service
    # - Publish delivers the message or raises an exception
    # - Consume processes to completion or dead-letters the message

    @deprecated("Use 'publish'")
    def publish_request(self, **kwargs):
        return self._publish_direct(
            self.requests_exchange,
            **kwargs
        )

    @deprecated("Use 'consume'")
    def consume_requests(self, **kwargs):
        return self._consume_direct(
            self.requests_exchange,
            **kwargs
        )

    # EVENTS are things that have happened:
    #   - Transient events fan-out to zero-many consuming services
    #   - Publish drops messages with no consumers

    @deprecated("Use 'publish'")
    def publish_event(self, **kwargs):
        return self.publish(**kwargs)

    @deprecated("Use 'maybe_publish'")
    def maybe_publish_event(self, **kwargs):
        return self.maybe_publish(**kwargs)

    @deprecated("Use 'consume'")
    def consume_events(self, queue: str, **kwargs):
        return self.consume(queue=queue, **kwargs)

    # Lower level handlers for REQUESTS and EVENTS

    def _publish_direct(self, exchange: str, **kwargs):
        semantics.publish_must_succeed(kwargs)
        return self._publish(exchange=exchange, **kwargs)

    def _consume_direct(
            self,
            exchange: str,
            *,
            queue: str,
            on_message_callback: Callable,
    ):
        self.queue_declare(
            queue,
            dead_letter_routing_key=queue,
            durable=True,
        )

        self.queue_bind(
            queue=queue,
            exchange=exchange,
            routing_key=queue,
        )

        return self._basic_consume(queue, on_message_callback)

    @cached_property
    def consumer_name(self) -> str:
        """Name for per-consumer fanout queues to this channel.
        May be overwritten or overridden (you'll actually have
        to if more than one channel per process consumes the
        same fanout "queue").
        """
        return ".".join(
            part for part in os.path.basename(sys.argv[0]).split("-")
            if part != "hive"
        )

    @cached_property
    def exclusive_queue_prefix(self) -> str:
        """Prefix for named exclusive queues on this channel.
        Should be the empty string for production environments.
        """
        envvar = "HIVE_EXCLUSIVE_QUEUE_PREFIX"
        result = os.environ.get(envvar, "").rstrip(".")
        if not result:
            return ""
        return f"{result}."

    # Exchanges

    @cache
    def _fanout_exchange_for(self, routing_key: str) -> str:
        return self._hive_exchange(
            exchange=routing_key,
            exchange_type="fanout",
            durable=True,
        )

    @cached_property
    def requests_exchange(self) -> str:
        return self._hive_exchange(
            exchange="requests",
            exchange_type="direct",
            durable=True,
        )

    @cached_property
    def dead_letter_exchange(self) -> str:
        return self._hive_exchange(
            exchange="dead.letter",
            exchange_type="direct",
            durable=True,
        )

    def _hive_exchange(self, exchange: str, **kwargs) -> str:
        name = f"hive.{exchange}"
        self.exchange_declare(exchange=name, **kwargs)
        return name

    # Queues

    def queue_declare(
            self,
            queue: str,
            *,
            dead_letter_routing_key: Optional[str] = None,
            arguments: Optional[dict[str, str]] = None,
            **kwargs
    ):
        if kwargs.get("exclusive", False) and queue:
            if (prefix := self.exclusive_queue_prefix):
                if not queue.hasprefix(prefix):
                    queue = f"{prefix}{queue}"

        if dead_letter_routing_key:
            DLX_ARG = "x-dead-letter-exchange"
            if arguments:
                if DLX_ARG in arguments:
                    raise ValueError(arguments)
                arguments = arguments.copy()
            else:
                arguments = {}

            dead_letter_queue = f"x.{dead_letter_routing_key}"
            self._pika.queue_declare(
                dead_letter_queue,
                durable=True,
            )

            dead_letter_exchange = self.dead_letter_exchange
            self.queue_bind(
                queue=dead_letter_queue,
                exchange=dead_letter_exchange,
                routing_key=dead_letter_routing_key,
            )

            arguments[DLX_ARG] = dead_letter_exchange

        if arguments:
            kwargs["arguments"] = arguments
        return self._pika.queue_declare(
            queue,
            **kwargs
        )

    def add_pre_publish_hook(self, hook: Callable):
        self._pre_publish_hooks.append(hook)

    def _publish(self, **kwargs):
        for hook in self._pre_publish_hooks:
            try:
                hook(self, **kwargs)
            except Exception:
                logger.exception("EXCEPTION")
        return self._basic_publish(**kwargs)

    def _basic_publish(
            self,
            *,
            message: bytes | dict,
            exchange: str = "",
            routing_key: str = "",
            content_type: Optional[str] = None,
            delivery_mode: DeliveryMode = DeliveryMode.Persistent,
            mandatory: bool = True,
    ):
        payload, content_type = self._encapsulate(message, content_type)
        return self.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=payload,
            properties=BasicProperties(
                content_type=content_type,
                delivery_mode=delivery_mode,  # Persist across broker restarts.
            ),
            mandatory=mandatory,  # Don't fail silently.
        )

    @staticmethod
    def _encapsulate(
            msg: bytes | dict,
            content_type: Optional[str],
    ) -> tuple[bytes, str]:
        """Prepare messages for transmission.
        """
        if not isinstance(msg, bytes):
            return json.dumps(msg).encode("utf-8"), "application/json"
        if not content_type:
            raise ValueError(f"content_type={content_type}")
        return msg, content_type

    @property
    def prefetch_count(self):
        return getattr(self, "_prefetch_count", None)

    @prefetch_count.setter
    def prefetch_count(self, value):
        if self.prefetch_count == value:
            return
        if self.prefetch_count is not None:
            raise ValueError(value)
        self.basic_qos(prefetch_count=value)
        self._prefetch_count = value

    def _basic_consume(
            self,
            queue: str,
            on_message_callback: Callable,
    ):
        self.prefetch_count = 1  # Receive one message at a time.

        def _wrapped_callback(channel: Channel, message: Message):
            delivery_tag = message.method.delivery_tag
            try:
                result = on_message_callback(channel, message)
                channel.basic_ack(delivery_tag=delivery_tag)
                return result
            except Exception as e:
                channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
                logged = False
                try:
                    if isinstance(e, NotImplementedError) and e.args:
                        traceback = e.__traceback__
                        while (next_tb := traceback.tb_next):
                            traceback = next_tb
                        code = traceback.tb_frame.f_code
                        try:
                            func = code.co_qualname
                        except AttributeError:
                            func = code.co_name  # Python <=3.10
                        logger.warning("%s:%s:UNHANDLED", func, e)
                        logged = True

                except Exception:
                    logger.exception("NESTED EXCEPTION")
                if not logged:
                    logger.exception("EXCEPTION")

        return self.basic_consume(
            queue=queue,
            on_message_callback=_wrapped_callback,
        )

    def basic_consume(
            self,
            queue: str,
            on_message_callback,
            *args,
            **kwargs
    ):
        def _wrapped_callback(channel, *args, **kwargs):
            assert channel is self._pika
            return on_message_callback(self, Message(*args, **kwargs))

        return self._pika.basic_consume(
            queue=queue,
            on_message_callback=_wrapped_callback,
            *args,
            **kwargs
        )
