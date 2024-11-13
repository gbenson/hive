import json
import time

from io import BytesIO

import pytest

from hive.messaging.schemas import ChatMessage


def test_new_event_stream(mock_server):
    wfile = BytesIO()
    with mock_server.new_event_stream(wfile) as stream:
        assert stream.last_activity == 0
        stream.send(b"499918f53a391e95")
        idle_time = time.time() - stream.last_activity
    assert idle_time > 0
    assert idle_time < 1
    assert wfile.getvalue() == b"499918f53a391e95"


@pytest.fixture
def mock_message():
    return ChatMessage(
        timestamp="2024-11-16 10:05:06Z",
        uuid="4317f794-74fc-4a5b-9af5-9dce54752ffe",
        text="hello, world",
    )


def test_send_initial_events(mock_server, mock_channel, mock_message):
    mock_message_json = mock_message.json()
    mock_channel.publish_event(
        routing_key="chat.messages",
        message=mock_message_json,
    )
    expect_msg = json.dumps(mock_message_json)

    wfile = BytesIO()
    with mock_server.new_event_stream(wfile) as stream:
        last_activity_1 = stream.last_activity
        assert last_activity_1 > 0
        idle_time_1 = time.time() - last_activity_1
        assert idle_time_1 > 0
        assert idle_time_1 < 1

        stream.send(b"okksdyxejpswqge7tahg")
        last_activity_2 = stream.last_activity
    idle_time_2 = time.time() - last_activity_2

    assert last_activity_2 > last_activity_1
    assert idle_time_2 > 0
    assert idle_time_2 < 1

    want_text = f"data: [{expect_msg}]\n\nokksdyxejpswqge7tahg"
    want_bytes = want_text.encode("utf-8")
    assert wfile.getvalue() == want_bytes
