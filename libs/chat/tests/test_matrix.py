import json

from hive.chat import ChatMessage
from hive.common import read_resource, parse_datetime


def read_event(filename):
    event = json.loads(read_resource(filename))
    if "specversion" in event:
        return event  # serialized CloudEvent
    return event["source"]  # lose matrix-commander additions


def test_basic():
    event = read_event("resources/text.json")
    message = ChatMessage.from_matrix_event(event)
    assert message.text == "hello world"
    assert message.html is None
    assert message.sender == "user"
    assert message.timestamp == parse_datetime("2024-10-30 00:26:28.020Z")
    assert message.in_reply_to is None
    assert message.matrix.json() == event
    assert not message.has_unhandled_fields
    assert ChatMessage.from_json(message.json()) == message


def test_html():
    event = read_event("resources/html.json")
    message = ChatMessage.from_matrix_event(event)
    assert message.text == "hello **WORLD**"
    assert message.html == "hello <strong>WORLD</strong>"
    assert message.sender == "user"
    assert message.timestamp == parse_datetime("2024-11-26 00:14:10.740Z")
    assert message.in_reply_to is None
    assert message.matrix.json() == event
    assert not message.has_unhandled_fields
    assert ChatMessage.from_json(message.json()) == message


def test_image():
    event = read_event("resources/image.json")
    message = ChatMessage.from_matrix_event(event)
    assert message.text == "Wi-Fi_QR_code_Guest.jpg"
    assert message.html is None
    assert message.sender == "user"
    assert message.timestamp == parse_datetime("2024-10-26 22:49:53.880Z")
    assert message.in_reply_to is None
    assert message.matrix.json() == event
    assert not message.has_unhandled_fields
    assert ChatMessage.from_json(message.json()) == message


def test_basic_cloudevent():
    event = read_event("resources/cloudevent.json")
    message = ChatMessage.from_matrix_event(event)
    assert message.text == "good morning"
    assert message.html is None
    assert message.sender == "user"
    assert message.timestamp == parse_datetime("2025-03-23T01:06:17.634Z")
    assert message.in_reply_to is None
    assert message.matrix.json() == event["data"]
    assert not message.has_unhandled_fields
    assert ChatMessage.from_json(message.json()) == message
