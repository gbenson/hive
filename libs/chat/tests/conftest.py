from __future__ import annotations

import sys

from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import namedtuple
from typing import Any

import pytest

MockEvent = namedtuple("MockEvent", ("routing_key", "message"))


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
            sys.modules["hive.chat.tell_user"],
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
class MockChannel:
    mock_messagebus: MockMessageBus

    def publish(self, *, routing_key: str, message: dict[str, Any]):
        event = MockEvent(routing_key, message)
        self.mock_messagebus.published_events.append(event)


@pytest.fixture
def mock_channel(mock_messagebus):
    with mock_messagebus.blocking_connection() as conn:
        yield conn.channel()
