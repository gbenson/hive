import pytest

from hive.messaging import Channel, Message


class MockChannel:
    def __init__(self):
        self.call_log = []

    def __getattr__(self, attr):
        return MockMethod(attr, self.call_log)


class MockMethod:
    def __init__(self, name, call_log):
        self.name = name
        self.call_log = call_log

    def __call__(self, *args, **kwargs):
        if self.name != "basic_publish":
            return
        assert not args
        assert not kwargs.pop("routing_key")
        routing_key = kwargs.pop("exchange")
        mandatory = kwargs.pop("mandatory", False)
        name = "publish_request" if mandatory else "publish_event"
        message = Message(method=None, **kwargs)
        self.call_log.append((name, routing_key, message.event()))


@pytest.fixture
def mock_channel():
    return Channel(MockChannel())
