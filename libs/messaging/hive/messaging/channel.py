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

    def send_to_queue(
            self,
            queue: str,
            msg: bytes | dict,
            content_type: Optional[str] = None,
            *,
            delivery_mode: DeliveryMode = DeliveryMode.Persistent,
            mandatory: bool = True,
    ):
        msg, content_type = self._encapsulate(msg, content_type)
        return self.basic_publish(
            exchange="",
            routing_key=queue,
            body=msg,
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
