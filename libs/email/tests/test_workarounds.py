"""Tests for workarounds for issues seen in the wild."""
from hive.email import load_email


def test_bad_message_id():
    """This breaks `email.policy.default`'s header parser.
    """
    msg = load_email(b"Message-ID: <[b3-JF=@example.com]>\r\n\r\n")
    assert msg.message_id == "<[b3-JF=@example.com]>"


def test_content_type_charset():
    """This breaks `email.policy.default.get_text_content()`.
    """
    msg = load_email(b'Content-Type: text/plain; charset=""\r\n\r\nX')
    assert msg.get_body(("plain",)).get_content() == "X"
