import pytest

from hive.chat_router.tokenizer import tokenize

from .util import T


@pytest.mark.parametrize(
    "user_input,expect_tokens",
    (("new email+password for smol (pls!)", (
        T("new", 0, 3),
        T("email", 4, 9),
        T("and", 9, 10),
        T("password", 10, 18),
        T("for", 19, 22),
        T("smol", 23, 27),
        T("(", 28, 29),
        T("please", 29, 32, False),
        T("!", 32, 33, False),
        T(")", 33, 34, False),
     )),
     ))
def test_disabbreviate(user_input, expect_tokens):
    expect_tokens = tuple(t.as_token(user_input) for t in expect_tokens)
    assert tuple(tokenize(user_input)) == expect_tokens
