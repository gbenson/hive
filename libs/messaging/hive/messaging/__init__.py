from .channel import Channel
from .connection import Connection
from .message_bus import MessageBus

DEFAULT_MESSAGE_BUS = MessageBus()

send_to_queue = DEFAULT_MESSAGE_BUS.send_to_queue
