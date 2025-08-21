from typing import Callable, TypeAlias

from .channel import Channel
from .message import Message


# Returned by pika.channel.Channel.basic_consume,
# "a tag which may be used to cancel the consumer".
# https://pika.readthedocs.io/en/stable/modules/channel.html
ConsumerTag: TypeAlias = str

OnMessageCallback: TypeAlias = Callable[[Channel, Message], None]
