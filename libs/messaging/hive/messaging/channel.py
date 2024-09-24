import json

from functools import cached_property
from typing import Callable, Optional

from pika import BasicProperties, DeliveryMode

from .wrapper import WrappedPikaThing
from .channel_services import Notifier


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

    def event_queue_declare(self, queue, **kwargs):
        result = self.queue_declare(queue, **kwargs)
        self.queue_bind(
            queue=queue,
            exchange=self.events_exchange,
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

    def publish_event(
            self,
            *,
            message: bytes | dict,
            routing_key: str,
            mandatory: bool,
            **kwargs
    ):
        return self._publish(
            message=message,
            exchange=self.events_exchange,
            routing_key=routing_key,
            mandatory=mandatory,
            **kwargs
        )

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
