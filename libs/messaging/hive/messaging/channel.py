import json
import logging

from functools import cached_property
from typing import Callable, Optional

from pika import BasicProperties, DeliveryMode
from pika.spec import Basic

from .wrapper import WrappedPikaThing
from .channel_services import Notifier

logger = logging.getLogger(__name__)
d = logger.debug


class Channel(WrappedPikaThing):
    @cached_property
    def notifier(self) -> Notifier:
        return Notifier(self)

    @cached_property
    def tell_user(self) -> Callable:
        return self.notifier.tell_user

    @cached_property
    def events_exchange(self) -> str:
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

    def _bound_queue_declare(self, queue, exchange, **kwargs):
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
            dead_letter_queue = f"x.{queue}"
            self.queue_declare(
                dead_letter_queue,
                durable=kwargs.get("durable", False),
            )

            dead_letter_exchange = self.dead_letter_exchange
            self.queue_bind(
                queue=dead_letter_queue,
                exchange=dead_letter_exchange,
                routing_key=queue,
            )

            arguments = kwargs.pop("arguments", {}).copy()
            self._ensure_arg(
                arguments,
                "x-dead-letter-exchange",
                dead_letter_exchange,
            )
            kwargs["arguments"] = arguments

        return self._pika.queue_declare(queue, **kwargs)

    def send_to_queue(
            self,
            queue: str,
            msg: bytes | dict,
            content_type: Optional[str] = None,
            **kwargs
    ):
        return self._publish(
            exchange="",
            routing_key=queue,
            message=msg,
            content_type=content_type,
            **kwargs
        )

    def publish_event(self, **kwargs):
        return self._publish(exchange=self.events_exchange, **kwargs)

    def publish_request(self, **kwargs):
        return self._publish(exchange=self.requests_exchange, **kwargs)

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

    def consume_events(self, *args, **kwargs):
        return self._basic_consume(self.events_exchange, *args, **kwargs)

    def consume_requests(self, *args, **kwargs):
        return self._basic_consume(self.requests_exchange, *args, **kwargs)

    def _basic_consume(
            self,
            exchange: str,
            queue: str,
            on_message_callback: Callable,
            *,
            durable_queue: bool = True,  # Persist across broker restarts.
            **queue_kwargs
    ):
        self.prefetch_count == 1  # Receive one message at a time.

        self._bound_queue_declare(
            queue=queue,
            exchange=exchange,
            durable=durable_queue,
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
            except Exception:
                channel.basic_reject(delivery_tag=delivery_tag, requeue=False)
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
