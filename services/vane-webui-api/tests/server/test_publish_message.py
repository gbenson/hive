import json

from datetime import datetime, timezone

import pytest

from hive.vane_webui_api.exceptions import HTTPError


def test_publish_valid_message(mock_server, mock_valkey):
    mock_server.publish_message_from_client({
        "sender": "user",
        "text": "test-76c36703b1ed",
        "uuid": "{c8c43dfd59e6492ca7b44e14384b099c}",
    })
    assert mock_valkey.keys() == {
        b"message:c8c43dfd-59e6-492c-a7b4-4e14384b099c",
        b"messages",
    }
    messages = mock_valkey[b"messages"]
    assert len(messages) == 1
    posix_timestamp, got_uuid = messages[0]
    assert got_uuid == b"c8c43dfd-59e6-492c-a7b4-4e14384b099c"
    timestamp = datetime.fromtimestamp(posix_timestamp, timezone.utc)

    message = mock_valkey[b"message:c8c43dfd-59e6-492c-a7b4-4e14384b099c"]
    assert json.loads(message.decode("utf-8")) == {
        "sender": "user",
        "text": "test-76c36703b1ed",
        "timestamp": str(timestamp),
        "uuid": "c8c43dfd-59e6-492c-a7b4-4e14384b099c",
    }


def test_html_is_dropped(mock_server, mock_valkey):
    mock_server.publish_message_from_client({
        "sender": "user",
        "text": "test-658421db963e0181",
        "html": "test-ab6c5113360ed42e",
        "uuid": "a1b7be8c3a5b41a0a085a5b1544a2575",
    })
    assert mock_valkey.keys() == {
        b"message:a1b7be8c-3a5b-41a0-a085-a5b1544a2575",
        b"messages",
    }
    messages = mock_valkey[b"messages"]
    assert len(messages) == 1
    posix_timestamp, got_uuid = messages[0]
    assert got_uuid == b"a1b7be8c-3a5b-41a0-a085-a5b1544a2575"
    timestamp = datetime.fromtimestamp(posix_timestamp, timezone.utc)

    message = mock_valkey[b"message:a1b7be8c-3a5b-41a0-a085-a5b1544a2575"]
    assert json.loads(message.decode("utf-8")) == {
        "sender": "user",
        "text": "test-658421db963e0181",
        "timestamp": str(timestamp),
        "uuid": "a1b7be8c-3a5b-41a0-a085-a5b1544a2575",
    }


@pytest.mark.parametrize("knockout_field", ("sender", "text", "uuid"))
def test_reject_any_missing_field(mock_server, mock_valkey, knockout_field):
    message = {
        "sender": "user",
        "text": "test-76c36703b1ed",
        "uuid": "{c8c43dfd59e6492ca7b44e14384b099c}",
    }
    message.pop(knockout_field)
    with pytest.raises(HTTPError) as excinfo:
        mock_server.publish_message_from_client(message)
    assert excinfo.value.status == 400
    cause = excinfo.value.__cause__
    assert isinstance(cause, KeyError)
    assert str(cause) == repr(knockout_field)
    assert not mock_valkey


@pytest.mark.parametrize("knockout_field", ("sender", "text", "uuid"))
def test_reject_any_mistyped_field(mock_server, mock_valkey, knockout_field):
    message = {
        "sender": "user",
        "text": "test-76c36703b1ed",
        "uuid": "{c8c43dfd59e6492ca7b44e14384b099c}",
    }
    message[knockout_field] = message[knockout_field].encode("utf-8")
    with pytest.raises(HTTPError) as excinfo:
        mock_server.publish_message_from_client(message)
    assert excinfo.value.status == 400
    assert isinstance(excinfo.value.__cause__, TypeError)
    assert not mock_valkey


def test_reject_bad_user(mock_server, mock_valkey):
    message = {
        "sender": "dave",
        "text": "test-76c36703b1ed",
        "uuid": "{c8c43dfd59e6492ca7b44e14384b099c}",
    }
    with pytest.raises(HTTPError) as excinfo:
        mock_server.publish_message_from_client(message)
    assert excinfo.value.status == 400
    cause = excinfo.value.__cause__
    assert isinstance(cause, ValueError)
    assert str(cause) == "dave"
    assert not mock_valkey


def test_reject_bad_uuid_variant(mock_server, mock_valkey):
    with pytest.raises(HTTPError) as excinfo:
        mock_server.publish_message_from_client({
            "sender": "user",
            "text": "test-76c36703b1ed",
            "uuid": "c8c43dfd-59e6-492c-17b4-4e14384b099c",
        })
    assert excinfo.value.status == 400
    assert not mock_valkey


def test_reject_bad_uuid_version(mock_server, mock_valkey):
    with pytest.raises(HTTPError) as excinfo:
        mock_server.publish_message_from_client({
            "sender": "user",
            "text": "test-76c36703b1ed",
            "uuid": "9842288a-a608-11ef-bf76-00163ebaab67",
        })
    assert excinfo.value.status == 400
    assert not mock_valkey
