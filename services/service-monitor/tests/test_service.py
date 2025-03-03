import json

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pytest

from hive.chat import ChatMessage
from hive.messaging import Message
from hive.service_monitor.service import Service


def test_normal_startup(mock_service, mock_channel):
    mock_service.send_test_event(mock_channel, {
        "meta": {
            "timestamp": "2024-11-15 19:47:06.750424+00:00",
            "uuid": "a7292305-41c7-48ec-8d21-56abd5cb59b5",
            "type": "service_status_report",
        },
        "service": "hive-service-monitor",
        "condition": "HEALTHY",
        "messages": ["Service started for the first time"],
    })
    assert mock_channel.tell_user_log == [((
        "service-monitor started for the first time",
    ), {
        "timestamp": datetime(
            2024, 11, 15, 19, 47, 6, 750424,
            tzinfo=timezone.utc,
        ),
        "uuid": UUID("a7292305-41c7-48ec-8d21-56abd5cb59b5"),
    })]


def test_report_without_messages(mock_service, mock_channel):
    mock_service.send_test_event(mock_channel, {
        "meta": {
            "timestamp": "2024-11-15 19:47:06.750424+00:00",
            "uuid": "a7292305-41c7-48ec-8d21-56abd5cb59b5",
            "type": "service_status_report",
        },
        "service": "hive-service-monitor",
        "condition": "HEALTHY",
    })
    assert mock_channel.tell_user_log == [((
        "service-monitor became HEALTHY",
    ), {
        "timestamp": datetime(
            2024, 11, 15, 19, 47, 6, 750424,
            tzinfo=timezone.utc,
        ),
        "uuid": UUID("a7292305-41c7-48ec-8d21-56abd5cb59b5"),
    })]


def test_rate_limiting(mock_service, mock_channel):
    mock_service.send_test_event(mock_channel, {
        "meta": {
            "timestamp": "2024-11-15 19:47:06.750424+00:00",
            "uuid": "a7292305-41c7-48ec-8d21-56abd5cb59b5",
            "type": "service_status_report",
        },
        "service": "hive-service-monitor",
        "condition": "HEALTHY",
        "messages": ["Service started for the first time"],
    })
    assert len(mock_channel.tell_user_log) == 1
    want_tell_user_log = str(mock_channel.tell_user_log)

    mock_service.send_test_event(mock_channel, {
        "meta": {
            "timestamp": "2024-11-15 19:47:06.850424+00:00",
            "uuid": "a7292305-41c7-48ec-8d21-58abd5cb59b5",
            "type": "service_status_report",
        },
        "service": "hive-service-monitor",
        "condition": "HEALTHY",
        "messages": ["Service started for the first time"],
    })
    assert len(mock_channel.tell_user_log) == 1
    assert str(mock_channel.tell_user_log) == want_tell_user_log


class MockValkey:
    def __init__(self):
        self._db = {}

    @staticmethod
    def _encode(value):
        if isinstance(value, str):
            value = value.encode("utf-8")
        assert isinstance(value, bytes)
        return value

    def set(self, key, value, *, ex=None, get=False):
        assert ex == 300
        assert get
        key, value = map(self._encode, (key, value))
        old_value = self._db.get(key)
        print(f"GET {key!r} => {old_value!r}")
        self._db[key] = value
        print(f"SET {key!r} <= {value!r}")
        return old_value


class MockChannel:
    def __init__(self):
        self.tell_user_log = []

    def publish(self, *, routing_key: str, message: dict[str, Any]):
        assert routing_key == "chat.messages"
        message = ChatMessage.from_json(message)
        self.tell_user_log.append(((message.text,), {
            "timestamp": message.timestamp,
            "uuid": message.uuid,
        }))


class MockService(Service):
    def send_test_event(self, channel, message):
        self.on_service_status_event(
            channel,
            Message(
                None,  # method: Basic.Deliver
                type("MockProperties", (), {
                    "content_type": "application/json",
                }),
                json.dumps(message).encode("utf-8"),
            ),
        )


@pytest.fixture
def mock_valkey():
    return MockValkey()


@pytest.fixture
def mock_service(mock_valkey):
    result = MockService()
    result._valkey = mock_valkey
    return result


@pytest.fixture
def mock_channel():
    return MockChannel()
