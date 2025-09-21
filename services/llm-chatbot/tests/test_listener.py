import json

from typing import Any
from unittest.mock import Mock

from hive.messaging import Message as HiveMessage

from hive.llm_chatbot.listener import Service


def test_update_context() -> None:
    channel = object()
    service = Service(db=Mock())

    service.on_request(channel, _encapsulate({
        "specversion": "1.0",
        "id": "7c88c4ba-8959-43fb-a361-0e5a1eaa67b2",
        "source": "https://gbenson.net/hive/services/chat-router",
        "type": "net.gbenson.hive.llm_chatbot_update_context_request",
        "time": "2025-09-12T22:45:26.683000+00:00",
        "data": {
            "context_id": "63960e88-32d5-4bf6-b951-2b045529e487",
            "message": {
                "id": "50937a35-3b37-4007-8aa8-99f67415f42b",
                "role": "user",
                "content": {"type": "text", "text": "Hello"},
            },
        },
    }))

    service.db.xadd.assert_called_once_with(
        "journal",
        {
            "action": "upsert_message",
            "context_id": "63960e88-32d5-4bf6-b951-2b045529e487",
            "message_id": "50937a35-3b37-4007-8aa8-99f67415f42b",
            "role": "user",
            "content.text": "Hello",
            "time": "2025-09-12T22:45:26.683Z",
        },
    )


def test_generate_response() -> None:
    channel = object()
    service = Service(db=Mock())

    service.on_request(channel, _encapsulate({
        "specversion": "1.0",
        "id": "7c88c4ba-8959-43fb-a361-0e5a1eaa67b2",
        "source": "https://gbenson.net/hive/services/chat-router",
        "type": "net.gbenson.hive.llm_chatbot_generate_response_request",
        "time": "2025-09-12T22:45:26.683000Z",
        "data": {"context_id": "63960e88-32d5-4bf6-b951-2b045529e487"},
    }))

    service.db.xadd.assert_called_once_with(
        "requests",
        {
            "action": "generate_response",
            "context_id": "63960e88-32d5-4bf6-b951-2b045529e487",
            "time": "2025-09-12T22:45:26.683Z",
        }
    )


# Utilities

def _encapsulate(event: dict[str, Any]) -> HiveMessage:
    return HiveMessage(
        None,
        Mock(content_type="application/cloudevents+json"),
        json.dumps(event).encode("utf-8"),
    )
