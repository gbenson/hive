import logging

import pytest

from hive.chat import ChatMessage
from hive.chat_router.handlers import ollama_router
from hive.chat_router.handlers.ollama_router import LLMInteraction
from hive.messaging.testing import blocking_connection  # noqa: F401

logger = logging.getLogger(__name__)
d = logger.info


def mock_tell_user(*args, **kwargs):
    d("mock_tell_user: %s, %s", args, kwargs)


def test_end_to_end(blocking_connection, monkeypatch):  # noqa: F811
    monkeypatch.setattr(ollama_router, "tell_user", mock_tell_user)
    interaction = LLMInteraction(ChatMessage("email for smol?"))
    with blocking_connection() as conn:
        channel = conn.channel()
        with pytest.raises(NotImplementedError):
            interaction._run(channel)
