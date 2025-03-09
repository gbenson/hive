import logging
import sys

import pytest

from hive.chat import ChatMessage
from hive.chat_router.handlers.ollama_router import (
    Intent,
    LLMHandler,
    LLMInteraction,
)
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


@pytest.mark.parametrize(
    "user_input,expect_intent",
    (("email for smol?", Intent.CREDS),
     ("dave's email?", Intent.CREDS),
     ("minecraft email?", Intent.CREDS),
     ("minecraft password", Intent.CREDS),
     ("slippy passwd", Intent.CREDS),
     ("sausages", None),
     ("draw sausages", Intent.IMAGE),
     ("imgaine sausages", Intent.IMAGE),
     ("imagine sausages", Intent.IMAGE),
     ("make a colouring page of sausages", Intent.IMAGE),
     ("make a coloring page of sausages", Intent.IMAGE),
     ("please draw a coloring page of sausages", Intent.IMAGE),
     ("please create a child's colouring page featuring a red kite",
      Intent.IMAGE),
     ("turn off the wifi", Intent.WIFI),
     ("wifi on pls", Intent.WIFI),
     ("wifi off pls", Intent.WIFI),
     ("cut the internet", Intent.WIFI),
     ("What's my screwfix password?", Intent.CREDS),
     ("What's my screw fix password?", Intent.CREDS),
     ("WiFi off", Intent.WIFI),
     ("WiFi on", Intent.WIFI),
     ("Make a colouring page of sausages", Intent.IMAGE),
     ("Please draw potato chips in the shape of Russian matrioshka dolls",
      Intent.IMAGE),
     ))
def test_guess_intent(user_input, expect_intent):
    handler = LLMHandler()
    assert handler.guess_intent(user_input) == expect_intent


@pytest.mark.parametrize(
    "user_input,expect_intent",
    (("email for smol?", "CREDS"),
     ("dave's email?", "CREDS"),
     ("minecraft email?", "CREDS"),
     ("minecraft password", "CREDS"),
     ("slippy passwd", "CREDS"),
     ("sausages", "UNKNOWN"),
     ("draw sausages", "IMAGE"),
     ("imgaine sausages", "IMAGE"),
     ("imagine sausages", "IMAGE"),
     ("make a colouring page of sausages", "IMAGE"),
     ("make a coloring page of sausages", "IMAGE"),
     ("please draw a coloring page of sausages", "IMAGE"),
     ("please create a child's colouring page featuring a red kite",
      "IMAGE"),
     ("turn off the wifi", "NET"),
     ("wifi on pls", "NET"),
     ("wifi off pls", "NET"),
     ("cut the internet", "NET"),
     ("What's my screwfix password?", "CREDS"),
     ("What's my screw fix password?", "CREDS"),
     ("WiFi off", "NET"),
     ("WiFi on", "NET"),
     ("Make a colouring page of sausages", "IMAGE"),
     ("Please draw potato chips in the shape of Russian matrioshka dolls",
      "IMAGE"),
     ))
def test_end_to_end(
        blocking_connection,  # noqa: F811
        interaction_collector,
        user_input,
        expect_intent,
):
    pytest.skip()
    handler = LLMHandler()
    message_handled = handler.handle(MockChannel(), ChatMessage(user_input))
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
    assert response == f"{interaction.name}: got intent: {expect_intent}"
