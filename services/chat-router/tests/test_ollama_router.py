import json
import logging
import sys

import pytest

from hive.chat import ChatMessage
from hive.chat_router.handlers.ollama_router import LLMHandler, LLMInteraction
from hive.messaging import Channel
from hive.messaging.testing import blocking_connection  # noqa: F401

logger = logging.getLogger(__name__)
d = logger.info


class MockChannel:
    pass


class InteractionCollector:
    def __init__(self, monkeypatch):
        self.interaction = None
        self.chat_responses = []

        def collect_interaction(interaction):
            assert self.interaction is None
            self.interaction = interaction

        monkeypatch.setattr(
            LLMInteraction,
            "start",
            collect_interaction,
        )

        monkeypatch.setattr(
            sys.modules["hive.chat.tell_user"],
            "_tell_user",
            self.collect_tell_user,
        )

    def collect_tell_user(self, _: Channel, message: ChatMessage):
        self.chat_responses.append(message)


@pytest.fixture
def interaction_collector(monkeypatch) -> InteractionCollector:
    yield InteractionCollector(monkeypatch)


def test_end_to_end(blocking_connection, interaction_collector):  # noqa: F811
    user_input = ChatMessage("email for smol?")

    handler = LLMHandler()
    message_handled = handler.handle(MockChannel(), user_input)
    assert message_handled
    interaction = interaction_collector.interaction
    assert interaction is not None

    with blocking_connection() as conn:
        channel = conn.channel()
        with pytest.raises(NotImplementedError):
            interaction._run(channel)

    assert len(interaction_collector.chat_responses) == 2
    # assert all(
    #     message.in_reply_to == input_message.uuid
    #     for message in interaction_collector.chat_responses
    # )

    response = interaction_collector.chat_responses[-1].text
    expect_prefix = f"{interaction.name}: got intent: "
    assert response.startswith(expect_prefix)

    intent = json.loads(response.removeprefix(expect_prefix))
    assert intent == {
        "primary": "Credential Management",
        "secondary": "Email address creation or lookup",
    }
