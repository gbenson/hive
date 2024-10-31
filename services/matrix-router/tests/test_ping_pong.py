import pytest

from hive.matrix_router.ping_pong import response_for_challenge


@pytest.mark.parametrize(
    "challenge,want_out",
    (("ping", "pong"),
     ("ping!", "pong!"),
     ("PiNG", "PoNG!!"),
     ("pINg", "pONg!!"),
     ("Bonjour", "Salop"),
     ("boNJOUr", "saLOp!!!!"),
     ("boNJOUr!", "saLOp!!!!!"),
     ("hello", "world"),
     ("helLO", "worLD!!"),
     ))
def test_ping_pong(challenge, want_out):
    assert response_for_challenge(challenge) == want_out
