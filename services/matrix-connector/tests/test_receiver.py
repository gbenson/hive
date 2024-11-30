import json
import sys

import pytest

from hive.common import parse_uuid, read_resource
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
    assert len(mock_channel.call_log) == 2
    _, _, kwargs = mock_channel.call_log[0]
    kwargs["message"] = json.loads(kwargs["message"])
    _, _, kwargs = mock_channel.call_log[1]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": event,
            "content_type": "application/json",
            "routing_key": "matrix.events.received",
            "mandatory": True,
        }),
        ("publish_event", (), {
            "message": {
                "text": "hello world",
                "sender": "user",
                "timestamp": "2024-10-30 00:26:28.020000+00:00",
                "uuid": uuid,
                "matrix": event["source"],
             },
            "routing_key": "chat.messages",
         }),
    ]


def test_html(mock_channel, mock_receiver):
    event = json.loads(read_resource("resources/html.json"))
    mock_receiver.on_matrix_event(event)
    assert len(mock_channel.call_log) == 2
    _, _, kwargs = mock_channel.call_log[0]
    kwargs["message"] = json.loads(kwargs["message"])
    _, _, kwargs = mock_channel.call_log[1]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": event,
            "content_type": "application/json",
            "routing_key": "matrix.events.received",
            "mandatory": True,
        }),
        ("publish_event", (), {
            "message": {
                "text": "hello **WORLD**",
                "html": "hello <strong>WORLD</strong>",
                "sender": "user",
                "timestamp": "2024-11-26 00:14:10.740000+00:00",
                "uuid": uuid,
                "matrix": event["source"],
             },
            "routing_key": "chat.messages",
         }),
    ]


def test_image(mock_channel, mock_receiver):
    event = json.loads(read_resource("resources/image.json"))
    with pytest.raises(ValueError) as excinfo:
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
    assert str(excinfo.value) == repr(event)


def test_redaction(mock_channel, mock_receiver):
    event = json.loads(read_resource("resources/redaction.json"))
    with pytest.raises(ValueError) as excinfo:
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
    assert str(excinfo.value) == repr(event)
