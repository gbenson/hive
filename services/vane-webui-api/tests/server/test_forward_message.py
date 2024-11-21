import json

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
    with mock_server.new_event_stream(None) as event_stream:
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

    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    actual_bytes = b"".join(mock_event_stream._send_queue)
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

    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    actual_bytes = b"".join(mock_event_stream._send_queue)
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
    message = MockMessage({
        "sender": "user",
        "text": "test-367b176c603ed",
        "uuid": "{c8c43dfd59e6492ca7b44e14384b099c}",
        "timestamp": "2024-11-19 20:17:41.928431Z",
    })
    with pytest.raises(ValueError) as excinfo:
        mock_server.forward_message_to_clients(mock_channel, message)
    assert not mock_valkey
    assert str(excinfo.value) == "{c8c43dfd59e6492ca7b44e14384b099c}"


def test_forward_basic_matrix_message(
        mock_server,
        mock_channel,
        mock_valkey,
        mock_event_stream,
):
    message = MockMessage({
        "text": "hello??",
        "sender": "user",
        "timestamp": "2024-11-21 19:22:36.273000+00:00",
        "uuid": "d546eef7-0c88-420f-a978-766a10b486be",
        "matrix": {
            "event_id": "$fMU2OhsGtVIE0FSKYxIG437NSwKQSB-pUPilX5WiyZA",
        },
    })
    expect_bytes = message.body
    mock_server.forward_message_to_clients(mock_channel, message)
    assert mock_valkey.keys() == {
        b"message:d546eef7-0c88-420f-a978-766a10b486be",
        b"messages",
    }
    assert mock_valkey[b"messages"] == [
        (1732216956.273, b"d546eef7-0c88-420f-a978-766a10b486be"),
    ]
    actual_bytes = mock_valkey[b"message:d546eef7-0c88-420f-a978-766a10b486be"]
    assert json.loads(actual_bytes) == {
        "text": "hello??",
        "sender": "user",
        "timestamp": "2024-11-21 19:22:36.273000+00:00",
        "uuid": "d546eef7-0c88-420f-a978-766a10b486be",
        "matrix": {
            "event_id": "$fMU2OhsGtVIE0FSKYxIG437NSwKQSB-pUPilX5WiyZA",
        },
    }
    assert actual_bytes == expect_bytes

    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    actual_bytes = b"".join(mock_event_stream._send_queue)
    assert actual_bytes == expect_bytes


def test_forward_html_matrix_message(
        mock_server,
        mock_channel,
        mock_valkey,
        mock_event_stream,
):
    message = MockMessage({
        "text": "**hello???**",
        "html": "<strong>hello???</strong>",
        "sender": "user",
        "timestamp": "2024-11-21 19:22:42.536000+00:00",
        "uuid": "ad9e31c0-370a-4bc7-a3ed-278d44808b79",
        "matrix": {
            "event_id": "$8ej4CrI-JWdWcyvzDj1Vf5IJwK2pCbEm1xyCTmpWr5Y",
        },
    })
    expect_bytes = message.body
    mock_server.forward_message_to_clients(mock_channel, message)
    assert mock_valkey.keys() == {
        b"message:ad9e31c0-370a-4bc7-a3ed-278d44808b79",
        b"messages",
    }
    assert mock_valkey[b"messages"] == [
        (1732216962.536, b"ad9e31c0-370a-4bc7-a3ed-278d44808b79"),
    ]
    actual_bytes = mock_valkey[b"message:ad9e31c0-370a-4bc7-a3ed-278d44808b79"]
    assert json.loads(actual_bytes) == {
        "text": "**hello???**",
        "html": "<strong>hello???</strong>",
        "sender": "user",
        "timestamp": "2024-11-21 19:22:42.536000+00:00",
        "uuid": "ad9e31c0-370a-4bc7-a3ed-278d44808b79",
        "matrix": {
            "event_id": "$8ej4CrI-JWdWcyvzDj1Vf5IJwK2pCbEm1xyCTmpWr5Y",
        },
    }
    assert actual_bytes == expect_bytes

    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    actual_bytes = b"".join(mock_event_stream._send_queue)
    assert actual_bytes == expect_bytes


def test_forward_matrix_message_with_null_html(
        mock_server,
        mock_channel,
        mock_valkey,
        mock_event_stream,
):
    message = MockMessage({
        "text": "hello?",
        "html": None,
        "sender": "user",
        "timestamp": "2024-11-21 19:19:28.579000+00:00",
        "uuid": "6c02632e-8bd7-4317-bc12-fa7b09d51de5",
        "matrix": {
            "event_id": "$YwfmtDfFwXNcd2dG7cBbO7GPRf-hsqoGLz6WSKDsVw0",
        },
    })
    expect_bytes = message.body
    mock_server.forward_message_to_clients(mock_channel, message)
    assert mock_valkey.keys() == {
        b"message:6c02632e-8bd7-4317-bc12-fa7b09d51de5",
        b"messages",
    }
    assert mock_valkey[b"messages"] == [
        (1732216768.579, b"6c02632e-8bd7-4317-bc12-fa7b09d51de5"),
    ]
    actual_bytes = mock_valkey[b"message:6c02632e-8bd7-4317-bc12-fa7b09d51de5"]
    assert json.loads(actual_bytes) == {
        "text": "hello?",
        "html": None,
        "sender": "user",
        "timestamp": "2024-11-21 19:19:28.579000+00:00",
        "uuid": "6c02632e-8bd7-4317-bc12-fa7b09d51de5",
        "matrix": {
            "event_id": "$YwfmtDfFwXNcd2dG7cBbO7GPRf-hsqoGLz6WSKDsVw0",
        },
    }
    assert actual_bytes == expect_bytes

    expect_bytes = b"data: [" + actual_bytes + b"]\n\n"
    actual_bytes = b"".join(mock_event_stream._send_queue)
    assert actual_bytes == expect_bytes
