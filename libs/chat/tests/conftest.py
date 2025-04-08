from __future__ import annotations

import sys

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

from hive.messaging import Channel


@dataclass
class MockEvent:
    type: str
    routing_key: str
    message: Optional[dict[str, Any]] = None
    data: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        assert (self.message is None) != (self.data is None)

    @property
    def cloudevent_data(self) -> Optional[dict[str, Any]]:
        return self.data


@dataclass
class MockMessageBus:
    published_events: list[MockEvent] = field(default_factory=list)

    @contextmanager
    def blocking_connection(self, **kwargs) -> MockConnection:
        yield MockConnection(self)


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
    mock_messagebus: MockMessageBus

    def channel(self) -> MockChannel:
        return MockChannel(self.mock_messagebus)


@dataclass
class MockChannel(Channel):
    mock_messagebus: MockMessageBus

    def publish_event(self, **kwargs):
        event = MockEvent("event", **kwargs)
        self.mock_messagebus.published_events.append(event)

    def publish_request(self, **kwargs):
        event = MockEvent("request", **kwargs)
        self.mock_messagebus.published_events.append(event)


@pytest.fixture
def mock_channel(mock_messagebus):
    with mock_messagebus.blocking_connection() as conn:
        yield conn.channel()
