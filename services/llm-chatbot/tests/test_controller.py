from unittest.mock import Mock

import pytest

from cloudevents.pydantic import CloudEvent
from cloudevents.conversion import to_json

from hive.messaging import Message

from hive.llm_chatbot.controller import Service


@pytest.mark.skip(reason="Incomplete")
def test_ollama_list() -> None:
    channel = Mock()
    service = Service()
    service.on_message(channel, _encapsulate("ollama list"))
    channel.send_text.assert_called_once_with(html="x")


# Utilities

def _encapsulate(command: str) -> Message:
    event = CloudEvent(
        data={
            "command": command,
            "created_from": {
                "event_id": "$JhD_uKJfiR8jmoF4MWbFDHMn9k48IhhTt57juv6BmiI",
                "room_id": "!RoBDTr33Tfqa27zzGK:matrix.org",
                "type": "net.gbenson.hive.matrix_event",
            },
        },
        source="",
        type="",
    )
    return Message(
        Mock(),
        Mock(content_type="application/cloudevents+json"),
        to_json(event),
    )
