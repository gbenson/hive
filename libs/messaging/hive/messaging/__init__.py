from .channel import Channel
from .connection import Connection
from .message_bus import MessageBus, Producer

DEFAULT_MESSAGE_BUS = MessageBus()

blocking_connection = DEFAULT_MESSAGE_BUS.blocking_connection
send_to_queue = DEFAULT_MESSAGE_BUS.send_to_queue

producer_connection = DEFAULT_MESSAGE_BUS.producer_connection
