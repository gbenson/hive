import json
import sys

import pytest

from pika import BasicProperties

from hive.common import parse_uuid, read_resource
from hive.matrix_connector.receiver import Receiver
from hive.messaging import Message


@pytest.fixture
def mock_receiver(mock_channel, mock_valkey):
    receiver = Receiver()
    receiver._channel = mock_channel
    receiver._valkey = mock_valkey
    try:
        yield receiver
    finally:
        sys.modules.pop("matrix_commander")


def message_from_event_bytes(event_bytes) -> Message:
    return Message(
        None,
        BasicProperties(
            content_type="application/json",
        ),
        event_bytes,
    )


def test_basic(mock_receiver, mock_channel, mock_valkey):
    event = json.loads(read_resource("resources/text.json"))

    # on_matrix_commander_output() publishes a Matrix event
    mock_receiver.on_matrix_commander_output(0, text=0, json_max=event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    assert kwargs.keys() == {"content_type", "message", "routing_key"}
    event_bytes = kwargs["message"]
    assert json.loads(event_bytes) == event

    # on_matrix_event() publishes a chat event
    message = message_from_event_bytes(event_bytes)
    mock_receiver.on_matrix_event(mock_channel, message)
    assert len(mock_channel.call_log) == 2

    _, _, kwargs = mock_channel.call_log[1]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish", (), {
            "message": event_bytes,
            "content_type": "application/json",
            "routing_key": "matrix.events",
        }),
        ("publish", (), {
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
    assert mock_valkey.call_log == [
        ("set", (
            f"message:{uuid}:event_id",
            "$NWixTiloQs5UwmlcdJfSfFVtw5SX3awbu3NXvDdOZwo",
        ), {
            "ex": 3600,
        }),
        ("set", (
            "event:$NWixTiloQs5UwmlcdJfSfFVtw5SX3awbu3NXvDdOZwo:message_id",
            uuid,
        ), {
            "ex": 3600,
        }),
    ]


def test_html(mock_receiver, mock_channel, mock_valkey):
    event = json.loads(read_resource("resources/html.json"))

    # on_matrix_commander_output() publishes a Matrix event
    mock_receiver.on_matrix_commander_output(0, text=0, json_max=event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    assert kwargs.keys() == {"content_type", "message", "routing_key"}
    event_bytes = kwargs["message"]
    assert json.loads(event_bytes) == event

    # on_matrix_event() publishes a chat event
    message = message_from_event_bytes(event_bytes)
    mock_receiver.on_matrix_event(mock_channel, message)

    _, _, kwargs = mock_channel.call_log[1]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish", (), {
            "message": event_bytes,
            "content_type": "application/json",
            "routing_key": "matrix.events",
        }),
        ("publish", (), {
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
    assert mock_valkey.call_log == [
        ("set", (
            f"message:{uuid}:event_id",
            "$r9Ul_OMug-vwLOY0yQY2kLtQtIFlxNff6nROekWc4Co",
        ), {
            "ex": 3600,
        }),
        ("set", (
            "event:$r9Ul_OMug-vwLOY0yQY2kLtQtIFlxNff6nROekWc4Co:message_id",
            uuid,
        ), {
            "ex": 3600,
        }),
    ]


def test_image(mock_receiver, mock_channel, mock_valkey):
    event = json.loads(read_resource("resources/image.json"))

    # on_matrix_commander_output() publishes a Matrix event
    mock_receiver.on_matrix_commander_output(0, text=0, json_max=event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    assert kwargs.keys() == {"content_type", "message", "routing_key"}
    event_bytes = kwargs["message"]
    assert json.loads(event_bytes) == event

    # on_matrix_event() publishes a chat event
    message = message_from_event_bytes(event_bytes)
    mock_receiver.on_matrix_event(mock_channel, message)

    _, _, kwargs = mock_channel.call_log[1]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish", (), {
            "message": event_bytes,
            "content_type": "application/json",
            "routing_key": "matrix.events",
        }),
        ("publish", (), {
            "message": {
                "text": "Wi-Fi_QR_code_Guest.jpg",
                "sender": "user",
                "timestamp": "2024-10-26 22:49:53.880000+00:00",
                "uuid": uuid,
                "matrix": event["source"],
             },
            "routing_key": "chat.messages",
         }),
    ]
    assert mock_valkey.call_log == [
        ("set", (
            f"message:{uuid}:event_id",
            "$pOp5KHHL3ECE3ZWtRw_PmnrH-mRqDFlDHcKgzMBSEVY",
        ), {
            "ex": 3600,
        }),
        ("set", (
            "event:$pOp5KHHL3ECE3ZWtRw_PmnrH-mRqDFlDHcKgzMBSEVY:message_id",
            uuid,
        ), {
            "ex": 3600,
        }),
    ]


def test_redaction(mock_receiver, mock_channel, mock_valkey):
    event = json.loads(read_resource("resources/redaction.json"))

    # on_matrix_commander_output() publishes a Matrix event
    mock_receiver.on_matrix_commander_output(0, text=0, json_max=event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    assert kwargs.keys() == {"content_type", "message", "routing_key"}
    event_bytes = kwargs["message"]
    assert json.loads(event_bytes) == event

    # on_matrix_event() doesn't publish a chat event
    message = message_from_event_bytes(event_bytes)
    mock_receiver.on_matrix_event(mock_channel, message)

    assert mock_channel.call_log == [
        ("publish", (), {
            "message": event_bytes,
            "content_type": "application/json",
            "routing_key": "matrix.events",
        }),
    ]
    assert mock_valkey.call_log == []
