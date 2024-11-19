import json

from uuid import uuid4

import pytest


@pytest.mark.parametrize("extra_checks", (False, True))
def test_login_flow(test_server, http_session, extra_checks):
    api_url = test_server.api_url
    session = http_session

    # Accessing the login URL without a session gets you a token.
    assert not session.cookies
    login_url = f"{api_url}/login"
    r = http_session.get(login_url)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    login_token = r.json().get("csrf")
    print(f"login_token = {login_token}")
    assert isinstance(login_token, str)
    assert login_token != "valid_csrf"
    assert len(login_token) > 40

    if extra_checks:
        # Hitting the login URL again gets you the same token as before.
        assert not session.cookies
        r = http_session.get(login_url)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"
        assert r.json().get("csrf") == login_token

        # Accessing other endpoints without a session gets you a 401.
        assert not session.cookies
        events_url = f"{api_url}/events"
        r = http_session.head(events_url)
        assert r.status_code == 401
        _ = r.text

        assert not session.cookies
        chat_url = f"{api_url}/chat"
        want_uuid = str(uuid4())
        want_message = {
            "sender": "user",
            "text": "hello world!",
            "uuid": want_uuid,
        }
        r = http_session.post(chat_url, json=want_message)
        assert r.status_code == 401

    # Logging in gets you a session.
    assert not session.cookies
    r = http_session.post(login_url, json={
        "user": "valid_username",
        "pass": "valid_password",
        "csrf": login_token,
    })
    assert r.status_code == 204
    session_id = session.cookies.get("sessionId")
    print(f"session_id = {session_id}")
    assert isinstance(session_id, str)
    assert len(session_id) > 40

    # Accessing the login URL with a session gets you a 204.
    r = http_session.get(login_url)
    assert r.status_code == 204
    assert session.cookies.get("sessionId") == session_id

    if extra_checks:
        # Chat now lets you post messages,
        r = http_session.post(chat_url, json=want_message)
        assert r.status_code == 204

        # Events should have the message we posted.
        r = http_session.get(events_url, stream=True)
        assert r.status_code == 200
        assert r.headers["content-type"] == "text/event-stream"
        buf, sep = bytearray(), b"\n\n"
        content = r.iter_content()
        while True:
            event, got_sep, rest = buf.partition(sep)
            if not got_sep:
                buf = event
                buf += next(content)
                continue
            event = event.decode("utf-8")
            event = event.split(":", 1)
            assert len(event) == 2
            assert event[0] == "data"
            for message in json.loads(event[1]):
                print(message)
                if message.get("uuid") == want_uuid:
                    break
            else:
                continue
            break
        timestamp = message.pop("timestamp", None)
        assert timestamp
        assert message == want_message
