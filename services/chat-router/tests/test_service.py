from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import Mock

from hive.chat_router import Service
from hive.messaging import Channel, Message


def make_test_message(
        matrix_event: dict[str, Any],
        *,
        routing_key: str = "matrix.events",
        subject: Optional[str] = None,
) -> Message:
    body, content_type = Channel._encapsulate(
        routing_key=routing_key,
        id="66e925ce-f0a1-4304-b4d5-43030c02bc8c",
        subject=subject or matrix_event.get("type"),
        data=matrix_event,
    )
    return Message(None, Mock(content_type=content_type), body)


def test_self_message():
    service = Service()
    mock_channel = Mock()
    service.on_matrix_event(mock_channel, make_test_message({
        "content": {"body": "salop", "msgtype": "m.text"},
        "event_id": "$fkvamdneqjwKqIg6rkO8bpRxhF6Mmr3GJC1fFKI7wwQ",
        "origin_server_ts": 1757455475575,
        "room_id": "!RoBDTr33Tfqa27zzGK:matrix.org",
        "sender": "@hive:gbenson.net",
        "type": "m.room.message",
        "unsigned": {
            "age": 199,
            "transaction_id": "mautrix-go_1757455475508388906_130",
        },
    }))

    mock_channel.publish_request.assert_called_once_with(
        type="net.gbenson.hive.chatbot_add_to_context_request",
        routing_key="chatbot.requests",
        time=datetime(2025, 9, 9, 22, 4, 35, 575000, tzinfo=timezone.utc),
        data={
            "role": "hive",
            "type": "text/plain",
            "content": "salop",
            "origin": {
                "id": "66e925ce-f0a1-4304-b4d5-43030c02bc8c",
                "source": "https://gbenson.net/hive/services/pytest",
                "type": "net.gbenson.hive.matrix_event",
            },
        },
    )
