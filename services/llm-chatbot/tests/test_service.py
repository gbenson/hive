import json

from typing import Any
from unittest.mock import Mock
from uuid import UUID

from hive.llm_chatbot import Service
from hive.messaging import Message as HiveMessage

from hive.llm_chatbot.schema import Message


def _encapsulate(event: dict[str, Any]) -> HiveMessage:
    return HiveMessage(
        None,
        Mock(content_type="application/cloudevents+json"),
        json.dumps(event).encode("utf-8"),
    )


def test_update_context() -> None:
    channel = Mock()
    service = Service(database=Mock())

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

    service.database.update_context.assert_called_once_with(
        UUID("63960e88-32d5-4bf6-b951-2b045529e487"),
        Message(
            id="50937a35-3b37-4007-8aa8-99f67415f42b",
            role="user",
            time="2025-09-12T22:45:26.683000+00:00",
            content={"type": "text", "text": "Hello"},
        ),
    )

    channel.assert_not_called()


def test_generate_response() -> None:
    channel = Mock()
    service = Service(database=Mock())

    service.on_request(channel, _encapsulate({
        "specversion": "1.0",
        "id": "7c88c4ba-8959-43fb-a361-0e5a1eaa67b2",
        "source": "https://gbenson.net/hive/services/chat-router",
        "type": "net.gbenson.hive.llm_chatbot_generate_response_request",
        "time": "2025-09-12T22:45:26.683000+00:00",
        "data": {"context_id": "63960e88-32d5-4bf6-b951-2b045529e487"},
    }))

    service.database.get_messages.assert_called_once_with(
        UUID("63960e88-32d5-4bf6-b951-2b045529e487"),
    )

    channel.send_text.assert_called_once_with(
        "idk what that is",
        sender="hive",
    )
