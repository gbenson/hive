from unittest.mock import Mock

import pytest

from hive.chat_router.brain import router
from hive.chat_router.service import Service

from .util import make_test_request


@pytest.mark.parametrize(
    "challenge,want_response",
    (("ping", "pong"),
     ("ping!", "pong!"),
     ("PiNG", "PoNG!"),
     ("pINg!", "pONg!"),
     ("Bonjour", "Salop"),
     ("boNJOUr", "saLOp!"),
     ("boNJOUr!", "saLOp!"),
     ("hello", "hi"),
     ("helLO", "hi!"),
     ("sALoP", "bOnJOuR!"),
     ("Hi", "Hello"),
     ("hi!", "hello!"),
     ("Hello?", "Hi!"),
     (" Hello ? ", "Hi!"),
     ("HeLlo?", "Hi!"),
     (" ponG ", "pinG!"),
     #
     ("pInG please", "pOnG!"),
     ("please piNg", "poNg!"),
     ("can you say ping?", 'you say "ping", I say "pong"!'),
     #
     ("pnig", "pong"),
     ("sallop!", "bonjour"),
     ("Heilo", "hi"),
     ))
def test_responses(challenge, want_response):
    mock_channel = Mock()
    router.dispatch(make_test_request(challenge), Service(), mock_channel)
    mock_channel.send_text.assert_called_once_with(want_response)
