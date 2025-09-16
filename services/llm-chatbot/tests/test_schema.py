from typing import Any

import pytest

from hive.llm_chatbot.schema import Message


@pytest.mark.parametrize(
    "message,expect_pairs", (
        (Message(
            id="50937a35-3b37-4007-8aa8-99f67415f42b",
            role="user",
            time="2025-09-12T22:45:26.683000+00:00",
            content={"type": "text", "text": "Hello"},
        ), {
            "id": "50937a35-3b37-4007-8aa8-99f67415f42b",
            "role": "user",
            "content.type": "text",
            "content.text": "Hello",
            "time": "2025-09-12T22:45:26.683000Z",
        }),
    ))
def test_message_as_key_value_pairs(
        message: Message,
        expect_pairs: dict[str, Any],
) -> None:
    assert message.as_key_value_pairs() == expect_pairs
