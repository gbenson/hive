import pytest

from hive.messaging import Channel
from hive.messaging.testing import LogDecoder as _LogDecoder, MockChannel

from hive.chat_router.pattern_graph import Matcher


class LogDecoder(_LogDecoder):
    @property
    def send_text(self) -> str:
        send_text_calls = [
            call
            for call in self.call_log
            if (call.method == "publish_request"
                and call.routing_key == "hive.matrix.send.text.requests")
        ]
        assert len(send_text_calls) == 1
        call = send_text_calls[0]
        return call.event.data["text"]


@pytest.fixture
def mock_channel():
    return Channel(MockChannel(LogDecoder))


@pytest.fixture
def no_spellcheck(monkeypatch):
    monkeypatch.setattr(Matcher, "SPELL_CHECK_MIN_WORD_LENGTH", 1_000_000)
