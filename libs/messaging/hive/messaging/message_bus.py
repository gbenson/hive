import os

from dataclasses import dataclass, field
from typing import Callable, Optional

from pika import (
    BlockingConnection,
    ConnectionParameters,
    PlainCredentials,
)
from pika.exceptions import AMQPConnectionError

from hive.common import read_config

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
        config = read_config(self.credentials_key)
        return PlainCredentials(
            config["default_user"],
            config["default_pass"],
        )

    def connection_params(
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
        params = self.connection_params(**kwargs)
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

    def tell_user(self, *args, **kwargs):
        with self.blocking_connection(connection_attempts=1) as conn:
            channel = conn.channel()
            return channel.tell_user(*args, **kwargs)
