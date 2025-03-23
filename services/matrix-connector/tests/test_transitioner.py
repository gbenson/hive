import json
import sys

import pytest

from cloudevents.conversion import to_json
from pika import BasicProperties

from hive.common import parse_uuid, read_resource
from hive.common.units import HOUR
from hive.matrix_connector.receiver import Receiver
from hive.matrix_connector.transitioner import Transitioner
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


@pytest.fixture
def mock_transitioner(mock_channel, mock_valkey):
    transitioner = Transitioner()
    transitioner._channel = mock_channel
    transitioner._valkey = mock_valkey
    return transitioner


def _testinputs(mock_channel, mock_receiver, filename):
    mc_event = json.loads(read_resource(filename))
    mock_receiver.on_matrix_commander_output(0, text=0, json_max=mc_event)
    assert len(mock_channel.call_log) == 1
    cloudevent = mock_channel.call_log.pop()[2]["message"]
    return mc_event["source"], Message(
        None,
        BasicProperties(
            content_type="application/cloudevents+json",
        ),
        to_json(cloudevent),
    )


def test_basic(mock_receiver, mock_transitioner, mock_channel, mock_valkey):
    matrix_event, message = _testinputs(
        mock_channel, mock_receiver, "resources/text.json"
    )

    # on_matrix_event() publishes a chat event
    mock_transitioner.on_matrix_event(mock_channel, message)

    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": {
                "text": "hello world",
                "sender": "user",
                "timestamp": "2024-10-30 00:26:28.020000+00:00",
                "uuid": uuid,
                "matrix": matrix_event,
             },
            "routing_key": "chat.messages",
         }),
    ]
    assert mock_valkey.call_log == [
        ("set", (
            f"message:{uuid}:event_id",
            "$NWixTiloQs5UwmlcdJfSfFVtw5SX3awbu3NXvDdOZwo",
        ), {
            "ex": 1 * HOUR,
        }),
        ("set", (
            "event:$NWixTiloQs5UwmlcdJfSfFVtw5SX3awbu3NXvDdOZwo:message_id",
            uuid,
        ), {
            "ex": 1 * HOUR,
        }),
    ]


def test_html(mock_receiver, mock_transitioner, mock_channel, mock_valkey):
    matrix_event, message = _testinputs(
        mock_channel, mock_receiver, "resources/html.json"
    )

    # on_matrix_event() publishes a chat event
    mock_transitioner.on_matrix_event(mock_channel, message)

    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": {
                "text": "hello **WORLD**",
                "html": "hello <strong>WORLD</strong>",
                "sender": "user",
                "timestamp": "2024-11-26 00:14:10.740000+00:00",
                "uuid": uuid,
                "matrix": matrix_event,
             },
            "routing_key": "chat.messages",
         }),
    ]
    assert mock_valkey.call_log == [
        ("set", (
            f"message:{uuid}:event_id",
            "$r9Ul_OMug-vwLOY0yQY2kLtQtIFlxNff6nROekWc4Co",
        ), {
            "ex": 1 * HOUR,
        }),
        ("set", (
            "event:$r9Ul_OMug-vwLOY0yQY2kLtQtIFlxNff6nROekWc4Co:message_id",
            uuid,
        ), {
            "ex": 1 * HOUR,
        }),
    ]


def test_image(mock_receiver, mock_transitioner, mock_channel, mock_valkey):
    matrix_event, message = _testinputs(
        mock_channel, mock_receiver, "resources/image.json"
    )

    # on_matrix_event() publishes a chat event
    mock_transitioner.on_matrix_event(mock_channel, message)

    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    uuid = str(parse_uuid(kwargs["message"]["uuid"]))
    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": {
                "text": "Wi-Fi_QR_code_Guest.jpg",
                "sender": "user",
                "timestamp": "2024-10-26 22:49:53.880000+00:00",
                "uuid": uuid,
                "matrix": matrix_event,
             },
            "routing_key": "chat.messages",
         }),
    ]
    assert mock_valkey.call_log == [
        ("set", (
            f"message:{uuid}:event_id",
            "$pOp5KHHL3ECE3ZWtRw_PmnrH-mRqDFlDHcKgzMBSEVY",
        ), {
            "ex": 1 * HOUR,
        }),
        ("set", (
            "event:$pOp5KHHL3ECE3ZWtRw_PmnrH-mRqDFlDHcKgzMBSEVY:message_id",
            uuid,
        ), {
            "ex": 1 * HOUR,
        }),
    ]


def test_redaction(
        mock_receiver,
        mock_transitioner,
        mock_channel,
        mock_valkey,
):
    matrix_event, message = _testinputs(
        mock_channel, mock_receiver, "resources/redaction.json"
    )

    # on_matrix_event() doesn't publish a chat event
    mock_transitioner.on_matrix_event(mock_channel, message)

    assert mock_channel.call_log == []
    assert mock_valkey.call_log == []
