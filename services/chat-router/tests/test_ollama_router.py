import logging

import pytest

from hive.chat import ChatMessage
from hive.chat_router.handlers import ollama_router
from hive.chat_router.handlers.ollama_router import LLMInteraction
from hive.messaging import blocking_connection

logger = logging.getLogger(__name__)
d = logger.info


def mock_tell_user(*args, **kwargs):
    d("mock_tell_user: %s, %s", args, kwargs)


@pytest.mark.skip
def test_end_to_end(monkeypatch):
    monkeypatch.setattr(ollama_router, "tell_user", mock_tell_user)
    interaction = LLMInteraction(ChatMessage("email for smol?"))
    with blocking_connection() as conn:
        interaction._run(conn.channel())
