from __future__ import annotations

import sys

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import pytest

from cloudevents.abstract import CloudEvent

from hive.messaging import Channel
from hive.messaging.testing import ChannelCall, MockChannel


@dataclass
class MockEvent:
    cc: ChannelCall

    @property
    def type(self) -> Literal["event", "request"]:
        return self.cc.method.removeprefix("publish_")

    @property
    def routing_key(self) -> str:
        """XXX HACK: Return the routing key the tests expect, i.e. the
        non-multiplexed Matrix requests queue this call would have been
        sent to before they were all multiplexed into "matrix.requests".
        """
        if self.cc.routing_key != "hive.matrix.requests":
            return self.cc.routing_key.removeprefix("hive.")

        prefix, _, base_type = self.cc.event.type.rpartition(".")
        assert prefix == "net.gbenson.hive"
        return f"{base_type.replace('_', '.')}s"

    @property
    def message(self) -> Optional[dict[str, Any]]:
        if self.cc.event:
            return None
        return self.cc.message.json()

    @property
    def cloudevent_data(self) -> Optional[dict[str, Any]]:
        return self.cc.event.data


@dataclass
class MockMessageBus:
    call_log: list[ChannelCall] = field(default_factory=list)

    @contextmanager
    def blocking_connection(self, **kwargs) -> MockConnection:
        yield MockConnection(self.call_log)

    @property
    def published_events(self) -> list[CloudEvent]:
        return list(map(MockEvent, self.call_log))


@pytest.fixture
def mock_messagebus(monkeypatch):
    with monkeypatch.context() as m:
        msgbus = MockMessageBus()
        m.setattr(
            sys.modules["hive.chat.util"],
            "blocking_connection",
            msgbus.blocking_connection,
        )
        yield msgbus


@dataclass
class MockConnection:
    call_log: list[ChannelCall] = field(default_factory=list)

    def channel(self) -> MockChannel:
        return Channel(MockChannel(call_log=self.call_log))


@pytest.fixture
def mock_channel(mock_messagebus):
    with mock_messagebus.blocking_connection() as conn:
        yield conn.channel()
