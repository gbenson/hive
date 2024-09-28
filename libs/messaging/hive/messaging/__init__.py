from pika.exceptions import UnroutableError

from .channel import Channel, Notifier
from .connection import Connection
from .message_bus import MessageBus, Producer

DEFAULT_MESSAGE_BUS = MessageBus()

blocking_connection = DEFAULT_MESSAGE_BUS.blocking_connection
publisher_connection = DEFAULT_MESSAGE_BUS.publisher_connection
send_to_queue = DEFAULT_MESSAGE_BUS.send_to_queue
tell_user = DEFAULT_MESSAGE_BUS.tell_user

producer_connection = DEFAULT_MESSAGE_BUS.producer_connection
