import pytest

from hive.chat_router.tokenizer import split

from .util import T


@pytest.mark.parametrize(
    "user_input,expect_tokens",
    (("", ()),

     ("hello?", (
         T("hello?", 0, 6),
     )),

     (" Hello ? ", (
         T("Hello", 1, 6),
         T("?", 7, 8),
     )),

     ("email for smol?", (
         T("email", 0, 5),
         T("for", 6, 9),
         T("smol?", 10, 15),
     )),

     ("🪲?", (
         T("🪲?", 0, 2),
     )),

     ("\tmake me\nan email+password \t for smol (pls!)", (
         T("make", 1, 5),
         T("me", 6, 8),
         T("an", 9, 11),
         T("email+password", 12, 26),
         T("for", 29, 32),
         T("smol", 33, 37),
         T("(pls!)", 38, 44),
     )),

     ("block @infomails.microsoft.com", (
         T("block", 0, 5),
         T("@infomails.microsoft.com", 6, 30),
     )),

     ("Es waren größtenteils 20 bis 24 m Länge.", (
         T("Es", 0, 2),
         T("waren", 3, 8),
         T("größtenteils", 9, 21),
         T("20", 22, 24),
         T("bis", 25, 28),
         T("24", 29, 31),
         T("m", 32, 33),
         T("Länge.", 34, 40),
     )),

     ))
def test_tokenize(user_input, expect_tokens):
    expect_tokens = tuple(t.as_token(user_input) for t in expect_tokens)
    assert tuple(split(user_input)) == expect_tokens
