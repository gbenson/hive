import json
import logging

from functools import cache, cached_property
from typing import Callable, Optional

from pika import BasicProperties, DeliveryMode
from pika.spec import Basic

from . import semantics
from .wrapper import WrappedPikaThing

logger = logging.getLogger(__name__)
d = logger.debug


class Channel(WrappedPikaThing):
    """The primary entry point for interacting with Hive's message bus.
    """
    # QUEUES are declared by their consuming service

    # CONSUME_* methods process to completion or dead-letter the message

    # REQUESTS are things we're asking to be done:
    # - Each request queue has exactly one consuming service
    # - Publish delivers the message or raises an exception
    # - Consume processes to completion or dead-letters the message

    def publish_request(self, **kwargs):
        return self._publish_direct(
            self.requests_exchange,
            **kwargs
        )

    def consume_requests(self, **kwargs):
        return self._consume_direct(
            self.requests_exchange,
            **kwargs
        )

    # EVENTS are things that have happened:
    # - DIRECT EVENTS have the same semantics as requests
    #
    # - FANOUT EVENTS are different:
    #   - Transient events fan-out to zero-many consuming services
    #   - Publish drops messages with no consumers

    def publish_event(self, **kwargs):
        if kwargs.pop("mandatory", False):
            return self._publish_direct(
                self.direct_events_exchange,
                **kwargs
            )

        semantics.publish_may_drop(kwargs)
        routing_key = kwargs["routing_key"]
        exchange = self._fanout_exchange_for(routing_key)
        return self._publish(exchange=exchange, **kwargs)

    def consume_events(self, **kwargs):
        if kwargs.pop("mandatory", False):
            return self._consume_direct(
                self.direct_events_exchange,
                **kwargs
            )

        routing_key = kwargs.pop("queue")
        exchange = self._fanout_exchange_for(routing_key)
        return self._basic_consume(
            exchange,
            queue="",  # broker choose a name
            **kwargs
        )

    # Common handlers for REQUESTS and DIRECT EVENTS

    def _publish_direct(self, exchange: str, **kwargs):
        semantics.publish_must_succeed(kwargs)
        return self._publish(exchange=exchange, **kwargs)

    def _consume_direct(self, exchange: str, **kwargs):
        return self._basic_consume(exchange, **kwargs)

    # Exchanges

    @cache
    def _fanout_exchange_for(self, routing_key: str) -> str:
        return self._hive_exchange(
            exchange=routing_key,
            exchange_type="fanout",
            durable=True,
        )

    @cached_property
    def direct_events_exchange(self) -> str:
        return self._hive_exchange(
            exchange="events",
            exchange_type="direct",
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

    def _bound_queue_declare(self, queue: str, exchange: str, **kwargs):
        ensure_kwarg = semantics._ensure_kwarg
        ensure_kwarg(kwargs, "dead_letter", True)

        if queue:
            # consumer-named queue (direct, permanent)
            ensure_kwarg(kwargs, "durable", True)
            ensure_kwarg(kwargs, "exclusive", False)
            dead_letter_basename = queue
        else:
            # broker-named queue (fanout, transient)
            ensure_kwarg(kwargs, "durable", False)
            ensure_kwarg(kwargs, "exclusive", True)
            dead_letter_basename = exchange.split(".", 1)[1]

        dead_letter_queue = f"x.{dead_letter_basename}"
        ensure_kwarg(kwargs, "dead_letter_queue", dead_letter_queue)

        result = self.queue_declare(queue, **kwargs)
        self.queue_bind(
            queue=queue,
            exchange=exchange,
            routing_key=queue,
        )
        return result

    def queue_declare(self, queue, **kwargs):
        dead_letter = kwargs.pop("dead_letter", False)
        if dead_letter:
            dead_letter_queue = kwargs.pop("dead_letter_queue")
            self.queue_declare(
                dead_letter_queue,
                durable=True,
            )

            dead_letter_exchange = self.dead_letter_exchange
            self.queue_bind(
                queue=dead_letter_queue,
                exchange=dead_letter_exchange,
                routing_key=dead_letter_queue.split(".", 1)[1]
            )

            arguments = kwargs.pop("arguments", {}).copy()
            self._ensure_arg(
                arguments,
                "x-dead-letter-exchange",
                dead_letter_exchange,
            )
            kwargs["arguments"] = arguments

        return self._pika.queue_declare(queue, **kwargs)

    def _publish(
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
    def _ensure_arg(args: dict, key: str, want_value: any):
        if args.get(key, want_value) != want_value:
            raise ValueError(args)
        args[key] = want_value

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
            exchange: str,
            *,
            queue: str,
            on_message_callback: Callable,
            **queue_kwargs
    ):
        self.prefetch_count = 1  # Receive one message at a time.

        self._bound_queue_declare(
            queue=queue,
            exchange=exchange,
            **queue_kwargs
        )

        def _wrapped_callback(
                channel: Channel,
                method: Basic.Deliver,
                *args,
                **kwargs
        ):
            delivery_tag = method.delivery_tag
            try:
                result = on_message_callback(channel, method, *args, **kwargs)
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
            return on_message_callback(type(self)(channel), *args, **kwargs)
        return self._pika.basic_consume(
            queue=queue,
            on_message_callback=_wrapped_callback,
            *args,
            **kwargs
        )


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
