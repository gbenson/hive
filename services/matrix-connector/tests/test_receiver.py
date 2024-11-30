import json
import sys

import pytest

from hive.common import read_resource
from hive.matrix_connector.receiver import Receiver


@pytest.fixture
def mock_receiver(mock_channel):
    receiver = Receiver()
    receiver._channel = mock_channel
    try:
        yield receiver
    finally:
        sys.modules.pop("matrix_commander")


def test_basic(mock_channel, mock_receiver):
    event = json.loads(read_resource("resources/text.json"))
    mock_receiver.on_matrix_event(event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    kwargs["message"] = json.loads(kwargs["message"])
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": event,
            "content_type": "application/json",
            "routing_key": "matrix.events.received",
            "mandatory": True,
        }),
    ]


def test_html(mock_channel, mock_receiver):
    event = json.loads(read_resource("resources/html.json"))
    mock_receiver.on_matrix_event(event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    kwargs["message"] = json.loads(kwargs["message"])
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": event,
            "content_type": "application/json",
            "routing_key": "matrix.events.received",
            "mandatory": True,
        }),
    ]


def test_image(mock_channel, mock_receiver):
    event = json.loads(read_resource("resources/image.json"))
    mock_receiver.on_matrix_event(event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    kwargs["message"] = json.loads(kwargs["message"])
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": event,
            "content_type": "application/json",
            "routing_key": "matrix.events.received",
            "mandatory": True,
        }),
    ]
