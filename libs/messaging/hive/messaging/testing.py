import pytest

from .message_bus import MessageBus


@pytest.fixture
def blocking_connection():
    def connect(**kwargs):
        kwargs["connection_attempts"] = 1
        try:
            return MessageBus().blocking_connection(**kwargs)
        except KeyError:
            pytest.skip("Message bus not configured")
        except ConnectionRefusedError as e:
            pytest.skip(f"Message bus not available: {e}")
    return connect
