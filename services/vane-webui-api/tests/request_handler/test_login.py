import pytest
import requests


def test_already_logged_in(mock_server, login_url):
    """GET with a valid session cookie returns no content.
    """
    r = requests.get(login_url, cookies={
        "sessionId": "f9e5d8c25951ac8c9d9856e346c437406a1316094bd0b",
    })
    assert r.status_code == 204
    assert "set-cookie" not in r.headers


@pytest.mark.parametrize(
    "cookies",
    ({},
     {"sessionId": "f9e5d8c25951ac8c9d9856e346c437406a1316094bd0a"},
     ))
def test_not_logged_in(mock_server, login_url, cookies):
    """GET without a valid session cookie returns a CSRF token.
    """
    r = requests.get(login_url, cookies=cookies)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    assert r.json() == {"csrf": "valid_csrf"}
    assert "set-cookie" not in r.headers


def test_login_success(mock_server, login_url):
    """POST with everything valid sets a session cookie.
    """
    r = requests.post(login_url, json={
        "user": "valid_user",
        "pass": "valid_pass",
        "csrf": "valid_csrf",
    })
    assert r.status_code == 204
    assert r.headers["set-cookie"] == "; ".join((
        "sessionId=f9e5d8c25951ac8c9d9856e346c437406a1316094bd0b",
        "HttpOnly",
        "Max-Age=2628000",
        "SameSite=strict",
        "Secure",
    ))


def test_failed_login(mock_server, login_url):
    """POST with anything wrong returns a new CSRF token.
    """
    r = requests.post(login_url, json={
        "user": "valid_user",
        "pass": "valid_pass",
        "csrf": "invalid_csrf",
    })
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"
    assert r.json() == {"csrf": "valid_csrf_2"}
    assert "set-cookie" not in r.headers
