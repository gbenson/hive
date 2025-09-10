import pytest

from hive.chat_router.brain import router
from hive.chat_router.service import Service

from .util import make_test_request


@pytest.mark.parametrize(
    "user_input",
    ("patterns",
     "patterns?",
     "what's you ptterns?",
     "what u patterns",
     "what's your paterns?",
     "whats ur patterns?",
     ))
def test_patterns(mock_channel, user_input):
    router.dispatch(make_test_request(user_input), Service(), mock_channel)
    assert mock_channel.expect.send_text.startswith("$:\n  *: <")
