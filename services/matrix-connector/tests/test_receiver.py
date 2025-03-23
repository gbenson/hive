import json
import sys

import pytest

from cloudevents.abstract import CloudEvent
from cloudevents.conversion import to_json
from pika import BasicProperties

from hive.common import read_resource
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
            content_type="application/cloudevents+json",
        ),
        event_bytes,
    )


@pytest.mark.parametrize(
    "event_basename",
    "text html image redaction".split(),
  )
def test_basic(mock_receiver, mock_channel, mock_valkey, event_basename):
    event = json.loads(read_resource(f"resources/{event_basename}.json"))

    # on_matrix_commander_output() publishes a Matrix event
    mock_receiver.on_matrix_commander_output(0, text=0, json_max=event)
    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    assert kwargs.keys() == {"message", "routing_key"}
    cloudevent = kwargs["message"]
    assert isinstance(cloudevent, CloudEvent)
    event_bytes = to_json(cloudevent)
    assert json.loads(event_bytes)["data"] == event["source"]

    assert mock_channel.call_log == [
        ("publish_event", (), {
            "message": cloudevent,
            "routing_key": "matrix.events",
        }),
    ]
    assert mock_valkey.call_log == []
