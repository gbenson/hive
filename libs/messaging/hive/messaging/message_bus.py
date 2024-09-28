import os

from dataclasses import dataclass, field
from typing import Callable, Optional

from pika import (
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
)
from pika.exceptions import AMQPConnectionError

from rstream import Producer

from hive.config import read as read_config

from .channel import Channel
from .connection import Connection, PublisherConnection


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

    # Queues

    def queue_connection_parameters(
            self,
            *,
            host: Optional[str] = None,
            port: Optional[int] = None,
            credentials: Optional[PlainCredentials] = None,
            connection_attempts: int = 5,  # * (socket_timeout
            retry_delay: float = 2.0,  # ...    + retry_delay) = 60 seconds
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
            connection_attempts=connection_attempts,
            retry_delay=retry_delay,
            heartbeat=heartbeat,
            blocked_connection_timeout=blocked_connection_timeout,
            **kwargs
        )

    def blocking_connection(
            self,
            *,
            connection_class: type[Connection] = Connection,
            on_channel_open: Optional[Callable[[Channel], None]] = None,
            **kwargs
    ) -> Connection:
        params = self.queue_connection_parameters(**kwargs)
        try:
            return connection_class(
                BlockingConnection(params),
                on_channel_open=on_channel_open,
            )
        except AMQPConnectionError as e:
            e = getattr(e, "args", [None])[0]
            e = getattr(e, "exception", None)
            if isinstance(e, (ConnectionRefusedError, TimeoutError)):
                raise e
            raise

    def publisher_connection(self, **kwargs) -> Connection:
        return self.blocking_connection(
            connection_class=PublisherConnection,
            **kwargs)

    def send_to_queue(self, queue: str, *args, **kwargs):
        durable = kwargs.pop("durable", True)
        with self.blocking_connection(connection_attempts=1) as conn:
            channel = conn.channel()
            channel.queue_declare(
                queue=queue,
                durable=durable,  # Persist across broker restarts.
            )
            return channel.send_to_queue(queue, *args, **kwargs)

    def tell_user(self, *args, **kwargs):
        with self.blocking_connection(connection_attempts=1) as conn:
            channel = conn.channel()
            return channel.tell_user(*args, **kwargs)

    # Streams

    def stream_connection_parameters(self, *, port: int = 5552, **kwargs):
        return self.queue_connection_parameters(port=port, **kwargs)

    def producer_connection(self, **kwargs) -> Producer:
        params = self.stream_connection_parameters(**kwargs)
        creds = params.credentials
        return Producer(
            host=params.host,
            username=creds.username,
            password=creds.password,
        )
