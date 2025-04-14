from dataclasses import dataclass, field

import pytest

from cloudevents.abstract import CloudEvent

from hive.messaging import Channel, Message


@dataclass(frozen=True)
class ChannelCall:
    method: str
    routing_key: str
    event: CloudEvent


@dataclass(frozen=True)
class LogDecoder:
    call_log: list[ChannelCall]

    @property
    def send_text(self) -> str:
        send_text_calls = [
            call
            for call in self.call_log
            if (call.method == "publish_request"
                and call.routing_key == "hive.matrix.send.text.requests")
        ]
        assert len(send_text_calls) == 1
        call = send_text_calls[0]
        return call.event.data["text"]


@dataclass(frozen=True)
class MockChannel:
    call_log: list[ChannelCall] = field(default_factory=list)

    def __getattr__(self, attr):
        return MockMethod(attr, self.call_log)

    @property
    def expect(self) -> LogDecoder:
        return LogDecoder(self.call_log)


@dataclass(frozen=True)
class MockMethod:
    name: str
    _call_log: list[ChannelCall]

    def __call__(self, *args, **kwargs) -> None:
        if self.name != "basic_publish":
            return
        assert not args
        assert not kwargs.pop("routing_key")
        routing_key = kwargs.pop("exchange")
        mandatory = kwargs.pop("mandatory", False)
        name = "publish_request" if mandatory else "publish_event"
        message = Message(method=None, **kwargs)
        self._call_log.append(ChannelCall(name, routing_key, message.event()))


@pytest.fixture
def mock_channel():
    return Channel(MockChannel())
