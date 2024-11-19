import json

from io import BytesIO

import pytest

from hive.messaging import Message


class MockProperties:
    content_type = "application/json"


class MockMessage(Message):
    def __init__(self, body):
        body = json.dumps(body).encode("utf-8")
        super().__init__(None, MockProperties, body)


@pytest.fixture
def mock_event_stream(mock_server):
    with mock_server.new_event_stream(BytesIO()) as event_stream:
        assert event_stream.last_activity == 0
        yield event_stream


@pytest.mark.parametrize("body_field", ("text", "html"))
def test_forward_valid_message(
        mock_server,
        mock_channel,
        mock_valkey,
        mock_event_stream,
        body_field,
):
    message = MockMessage({
        "sender": "user",
        body_field: "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
        "unHaNDlEd": 42,
    })
    expect_bytes = message.body
    mock_server.forward_message_to_clients(mock_channel, message)
    assert mock_valkey.keys() == {
        b"message:c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        b"messages",
    }
    assert mock_valkey[b"messages"] == [
        (1732047461.928431, b"c8c43dfd-59e6-492c-a7b4-4e14384b099c"),
    ]
    actual_bytes = mock_valkey[b"message:c8c43dfd-59e6-492c-a7b4-4e14384b099c"]
    assert json.loads(actual_bytes) == {
        "sender": "user",
        body_field: "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
        "unHaNDlEd": 42,
    }
    assert actual_bytes == expect_bytes

    assert mock_event_stream.last_activity > 0
    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    with mock_event_stream._lock:
        actual_bytes = mock_event_stream._wfile.getvalue()
    assert actual_bytes == expect_bytes


def test_remove_double_newlines(
        mock_server,
        mock_channel,
        mock_valkey,
        mock_event_stream,
):
    message = MockMessage({
        "sender": "olivia_squizzle",
        "text": "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    })
    expect_bytes = message.body
    assert b"\n\n" not in expect_bytes
    message.body = expect_bytes.replace(b'"uuid"', b'\n\n"uuid"')
    assert b"\n\n" in message.body
    assert message.body != expect_bytes

    mock_server.forward_message_to_clients(mock_channel, message)
    assert mock_valkey.keys() == {
        b"message:c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        b"messages",
    }
    assert mock_valkey[b"messages"] == [
        (1732047461.928431, b"c8c43dfd-59e6-492c-a7b4-4e14384b099c"),
    ]
    actual_bytes = mock_valkey[b"message:c8c43dfd-59e6-492c-a7b4-4e14384b099c"]
    assert json.loads(actual_bytes) == {
        "sender": "olivia_squizzle",
        "text": "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    }
    assert actual_bytes == expect_bytes
    assert b"\n\n" not in actual_bytes

    assert mock_event_stream.last_activity > 0
    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    with mock_event_stream._lock:
        actual_bytes = mock_event_stream._wfile.getvalue()
    assert actual_bytes == expect_bytes


@pytest.mark.parametrize(
    "knockout_field", ("sender", "text", "uuid", "timestamp"),
)
def test_reject_any_missing_field(
        mock_server,
        mock_channel,
        mock_valkey,
        knockout_field,
):
    message = {
        "sender": "user",
        "text": "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    }
    message.pop(knockout_field)
    message = MockMessage(message)
    with pytest.raises(ValueError):
        mock_server.forward_message_to_clients(mock_channel, message)
    assert not mock_valkey


def test_reject_mistyped_message(
        mock_server,
        mock_channel,
        mock_valkey,
):
    message = MockMessage(tuple({
        "sender": "user",
        "text": "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    }.items()))
    with pytest.raises(TypeError):
        mock_server.forward_message_to_clients(mock_channel, message)
    assert not mock_valkey


@pytest.mark.parametrize(
    "knockout_field", ("sender", "text", "uuid", "timestamp"),
)
def test_reject_any_mistyped_value(
        mock_server,
        mock_channel,
        mock_valkey,
        knockout_field,
):
    message = {
        "sender": "user",
        "text": "test-367b176c603ed",
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    }
    message[knockout_field] = 1
    message = MockMessage(message)
    with pytest.raises(TypeError):
        mock_server.forward_message_to_clients(mock_channel, message)
    assert not mock_valkey


def test_reject_oddformat_uuid(
        mock_server,
        mock_channel,
        mock_valkey,
):
    message = {
        "sender": "user",
        "text": "test-367b176c603ed",
        "uuid": "{c8c43dfd59e6492ca7b44e14384b099c}",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    }
    message = MockMessage(message)
    with pytest.raises(ValueError) as excinfo:
        mock_server.forward_message_to_clients(mock_channel, message)
    assert not mock_valkey
    assert str(excinfo.value) == "{c8c43dfd59e6492ca7b44e14384b099c}"
