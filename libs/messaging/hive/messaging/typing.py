from typing import Any, Callable, TypeAlias, Protocol

from .channel import Channel
from .connection import Connection
from .message import Message


class ConnectionFactory(Protocol):
    def __call__(self, **kwargs: Any) -> Connection: ...


# Returned by pika.channel.Channel.basic_consume,
# "a tag which may be used to cancel the consumer".
# https://pika.readthedocs.io/en/stable/modules/channel.html
ConsumerTag: TypeAlias = str

OnChannelOpenCallback: TypeAlias = Callable[[Channel], None]
OnMessageCallback: TypeAlias = Callable[[Channel, Message], None]
