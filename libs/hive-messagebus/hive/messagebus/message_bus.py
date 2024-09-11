import json
import logging
import os

from contextlib import closing
from dataclasses import dataclass, field
from typing import Optional

from pika import (
    BasicProperties,
    BlockingConnection,
    ConnectionParameters,
    DeliveryMode,
    PlainCredentials,
)

from hive.config import read as read_config

logger = logging.getLogger(__name__)


@dataclass
class MessageBus:
    host: str = field(
        default_factory=lambda: os.environ.get(
            "RABBITMQ_HOST", "rabbit"),
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get(
            "RABBITMQ_PORT",
            str(ConnectionParameters.DEFAULT_PORT))),
    )
    credentials_key: str = "rabbitmq"

    @property
    def credentials(self):
        env = read_config(self.credentials_key)
        return PlainCredentials(
            env["RABBITMQ_DEFAULT_USER"],
            env["RABBITMQ_DEFAULT_PASS"],
        )

    def blocking_connection(self, **kwargs) -> BlockingConnection:
        for key in ("host", "port", "credentials"):
            if key in kwargs:
                continue
            kwargs[key] = getattr(self, key)

        params = ConnectionParameters(**kwargs)
        return BlockingConnection(params)

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

    def send_to_queue(
            self,
            queue: str,
            msg: bytes | dict,
            content_type: Optional[str] = None,
            *,
            durable: bool = True,
            mandatory: bool = True,
    ):
        msg, content_type = self._encapsulate(msg, content_type)
        with closing(self.blocking_connection()) as conn:
            channel = conn.channel()
            channel.queue_declare(
                queue=queue,
                durable=durable,  # persist across broker restarts
            )
            channel.confirm_delivery()  # don't fail silently
            channel.basic_publish(
                exchange="",  # ChannelClosedByBroker: (404, "NOT_FOUND...
                routing_key=queue,  # UnroutableError: ...
                body=msg,
                properties=BasicProperties(
                    content_type=content_type,
                    delivery_mode=DeliveryMode.Persistent,
                ),
                mandatory=mandatory,  # don't fail silently
            )
