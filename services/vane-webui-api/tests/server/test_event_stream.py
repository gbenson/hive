import json
import time

from io import BytesIO
from threading import Thread

import pytest

from hive.chat import ChatMessage


def get_stream_output(stream, timeout=5, poll_interval=0.5):
    thread = Thread(target=stream.run, daemon=True)
    thread.start()
    deadline = time.time() + timeout
    while stream.is_open and time.time() < deadline:
        with stream._lock:
            if not stream._send_queue:
                stream.is_open = False
        time.sleep(poll_interval)
    thread.join(timeout=max(deadline - time.time(), poll_interval))
    result = stream._wfile.getvalue()
    stream._wfile = BytesIO()
    stream.is_open = True
    return result


def test_new_event_stream(mock_server):
    wfile = BytesIO()
    with mock_server.new_event_stream(wfile) as stream:
        assert get_stream_output(stream) == b"event: keepalive\ndata:\n\n"
        stream.send(b"499918f53a391e95")
        assert get_stream_output(stream) == b"499918f53a391e95"


@pytest.fixture
def mock_message():
    return ChatMessage(
        timestamp="2024-11-16 10:05:06Z",
        uuid="4317f794-74fc-4a5b-9af5-9dce54752ffe",
        text="hello, world",
    )


@pytest.mark.parametrize("two_step", (False, True))
def test_send_initial_events(
        mock_server,
        mock_channel,
        mock_message,
        two_step,
):
    mock_message_json = mock_message.json()
    mock_channel.publish_event(
        routing_key="chat.messages",
        message=mock_message_json,
    )
    expect_msg_1 = json.dumps(mock_message_json)
    expect_sent = f"data: [{expect_msg_1}]\n\n".encode()

    wfile = BytesIO()
    with mock_server.new_event_stream(wfile) as stream:
        if two_step:
            assert get_stream_output(stream) == expect_sent
            expect_sent = b""

        expect_msg_2 = b"okksdyxejpswqge7tahg"
        stream.send(expect_msg_2)
        expect_sent += expect_msg_2
        assert get_stream_output(stream) == expect_sent
