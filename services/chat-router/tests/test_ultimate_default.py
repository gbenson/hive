from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import Mock

from hive.common import parse_datetime

from hive.chat_router.brain import router
from hive.chat_router.service import Service


@dataclass(frozen=True)
class Request:
    text: str
    time: datetime
    room_id: str
    event_id: str


def test_ultimate_default(no_spellcheck):
    mock_request = Request(
        text="24veee4g7583burphz6ijx5unvzh77hi",
        time=parse_datetime("2024-09-02 11:10:31.186283Z"),
        room_id="!RoBDTr33Tfqa27zzGK:matrix.org",
        event_id="$fkvamdneqjwKqIg6rkO8bpRxhF6Mmr3GJC1fFKI7wwQ",
    )
    mock_channel = Mock()
    router.dispatch(mock_request, Service(), mock_channel)

    mock_channel.publish_request.assert_called_once_with(
        type="net.gbenson.hive.llm_chatbot_generate_response_request",
        routing_key="llm.chatbot.requests",
        time=datetime(2024, 9, 2, 11, 10, 31, 186283, tzinfo=timezone.utc),
        data={
            "context_id": "63960e88-32d5-4bf6-b951-2b045529e487",
            "message_id": "5bdd0f8d-340e-4bea-abb3-adf96de62d94",
        },
    )
