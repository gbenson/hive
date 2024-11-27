import pytest

from hive.chat_router.handlers.ping import PingHandler


@pytest.mark.parametrize(
    "challenge,want_out",
    (("", None),
     ("He'ershingenmosiken", None),
     ("ping", "pong"),
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
     ))
def test_responses(challenge, want_out):
    assert PingHandler.response_for_challenge(challenge) == want_out
