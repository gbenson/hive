import os

from dataclasses import dataclass, field
from typing import Optional

from pika import (
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
)
from pika.exceptions import AMQPConnectionError

from hive.config import read as read_config

from .connection import Connection


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
        try:
            return Connection(BlockingConnection(params))
        except AMQPConnectionError as e:
            e = getattr(e, "args", [None])[0]
            e = getattr(e, "exception", None)
            if isinstance(e, (ConnectionRefusedError, TimeoutError)):
                raise e
            raise

    def send_to_queue(self, queue: str, *args, **kwargs):
        durable = kwargs.pop("durable", True)
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.queue_declare(
                queue=queue,
                durable=durable,  # Persist across broker restarts.
            )
            return channel.send_to_queue(queue, *args, **kwargs)
