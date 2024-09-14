import json
import logging
import os

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

from .connection import Connection

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
    def credentials(self) -> PlainCredentials:
        env = read_config(self.credentials_key)
        return PlainCredentials(
            env["RABBITMQ_DEFAULT_USER"],
            env["RABBITMQ_DEFAULT_PASS"],
        )

    def connection_parameters(
            self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            credentials: Optional[PlainCredentials] = None,
            heartbeat: int = 600,
            blocked_connection_timeout: int = 300,
            **kwargs
    ) -> ConnectionParameters:
        if not host:
            host = self.host
        if not port:
            port = self.port
        if not credentials:
            credentials = self.credentials

        return ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
            heartbeat=heartbeat,
            blocked_connection_timeout=blocked_connection_timeout,
            **kwargs
        )

    def blocking_connection(self, **kwargs) -> Connection:
        params = self.connection_parameters(**kwargs)
        return Connection(BlockingConnection(params))

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
        with self.blocking_connection() as conn:
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
