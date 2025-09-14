from unittest.mock import Mock
from uuid import UUID

from hive.llm_chatbot.database import Database
from hive.llm_chatbot.schema import Message


def test_update_context() -> None:
    db = Database(Mock())
    db.update_context(
        UUID("63960e88-32d5-4bf6-b951-2b045529e487"),
        Message(
            id="50937a35-3b37-4007-8aa8-99f67415f42b",
            role="user",
            time="2025-09-12T22:45:26.683000+00:00",
            content={"type": "text", "text": "Hello"},
        ),
    )
    db._vk.xadd.assert_called_once_with(
        "ctx:63960e88-32d5-4bf6-b951-2b045529e487:log",
        {
            "cmd": "update",
            "id": "50937a35-3b37-4007-8aa8-99f67415f42b",
            "role": "user",
            "content.text": "Hello",
            "time": "2025-09-12T22:45:26.683000Z",
        },
    )
