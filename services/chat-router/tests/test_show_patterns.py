from unittest.mock import Mock

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
def test_patterns(user_input):
    mock_channel = Mock()
    router.dispatch(make_test_request(user_input), Service(), mock_channel)
    mock_channel.send_text.assert_called_once()
    assert mock_channel.send_text.call_args.args[0].startswith("$:\n  *: <")
