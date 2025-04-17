import pytest

from hive.chat_router.brain import router
from hive.chat_router.service import Service


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
def test_responses(mock_channel, challenge, want_response):
    router.dispatch(challenge, Service(), mock_channel)
    assert mock_channel.expect.send_text == want_response
