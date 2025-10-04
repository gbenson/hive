from unittest.mock import Mock

from cloudevents.pydantic import CloudEvent

from hive.common import parse_datetime

from hive.chat_router import Service


class Command(CloudEvent):
    def __init__(self, text: str):
        super().__init__(
            data={
                "content": {
                    "body": text,
                    "msgtype": "m.text"
                },
                "event_id": "$JhD_uKJfiR8jmoF4MWbFDHMn9k48IhhTt57juv6BmiI",
                "origin_server_ts": 1725275431186,
                "room_id": "!RoBDTr33Tfqa27zzGK:matrix.org",
                "sender": "@gary:gbenson.net",
                "type": "m.room.message",
            },
            source="",
            type="net.gbenson.hive.matrix_event",
        )


def test_ollama_list(test_config) -> None:
    mock_channel = Mock()
    Service().on_room_message(mock_channel, Command("ollama list"))
    mock_channel.publish_request.assert_called_with(
        data={
            "command": "ollama list",
            "created_from": {
                "event_id": "$JhD_uKJfiR8jmoF4MWbFDHMn9k48IhhTt57juv6BmiI",
                "room_id": "!RoBDTr33Tfqa27zzGK:matrix.org",
                "type": "net.gbenson.hive.matrix_event",
            },
        },
        routing_key="llm.chatbot.ollama.commands",
        time=parse_datetime("2024-09-02 11:10:31.186Z"),
    )
