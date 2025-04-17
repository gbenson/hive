import pytest

from hive.chat_router.brain import router


@pytest.mark.xfail(reason="not implemented")  # XXX
@pytest.mark.parametrize(
    "user_input,want_call",
    (("generate two random words", "pong"),
     ("please generate 4 random words", "pong"),
     ("can you create a random word please", "pong"),
     ("generate a random male name", "x"),
     ("random word", "y"),
     ("random verb", "y"),
     ("four nouns?", "y"),
     ("gender-neutral name?", "y"),
     ("neutral name?", "y"),
     ))
def test_responses(user_input, want_call):
    receiver = type("MockReceiver", (), {})()
    router.dispatch(user_input, receiver=receiver)
    assert receiver.got_call == want_call
