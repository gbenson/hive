import pytest

from pika.exceptions import AMQPConnectionError

from .message_bus import MessageBus


@pytest.fixture
def blocking_connection():
    def connect(**kwargs):
        kwargs["connection_attempts"] = 1
        try:
            return MessageBus().blocking_connection(**kwargs)
        except ConnectionRefusedError as e:
            pytest.skip(f"No message bus: {e}")
    return connect
