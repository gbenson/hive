from pika.exceptions import UnroutableError

from .channel import Channel
from .connection import Connection
from .message import Message
from .message_bus import MessageBus

DEFAULT_MESSAGE_BUS = MessageBus()

blocking_connection = DEFAULT_MESSAGE_BUS.blocking_connection
publisher_connection = DEFAULT_MESSAGE_BUS.publisher_connection

tell_user = DEFAULT_MESSAGE_BUS.tell_user
