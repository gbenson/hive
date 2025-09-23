from pathlib import Path
from textwrap import dedent

import pytest

from hive.common.testing import test_config_dir  # noqa: F401
from hive.messaging import Channel
from hive.messaging.testing import LogDecoder as _LogDecoder, MockChannel

from hive.chat_router.pattern_graph import Matcher


@pytest.fixture(autouse=True)
def test_config(test_config_dir):  # noqa: F811
    (Path(test_config_dir) / "chatbot.yml").write_text(dedent("""\
        chatbot:
          users:
            user:
              matrix_id: "@gary:gbenson.net"
              role: user
            hive:
              matrix_id: "@hive:gbenson.net"
              role: hive
        """))


class LogDecoder(_LogDecoder):
    @property
    def send_text(self) -> str:
        published_events = [
            call.message.event()
            for call in self.call_log
            if (call.method == "publish_request"
                and call.routing_key == "hive.matrix.requests")
        ]
        send_text_events = [
            event
            for event in published_events
            if event.type == "net.gbenson.hive.matrix_send_text_request"
        ]
        assert len(send_text_events) == 1
        event = send_text_events[0]
        return event.data["text"]


@pytest.fixture
def mock_channel():
    mock_channel = MockChannel(LogDecoder)
    channel = Channel(mock_channel)
    channel.call_log = mock_channel.call_log
    return channel


@pytest.fixture
def no_spellcheck(monkeypatch):
    monkeypatch.setattr(Matcher, "SPELL_CHECK_MIN_WORD_LENGTH", 1_000_000)
