from http import HTTPStatus

import pytest

from hive.vane_webui_api.exceptions import HTTPError
from hive.vane_webui_api.request_handler import RequestHandler


class MockHeaders:
    def __init__(self, cookie_headers=None, sep="="):
        if cookie_headers is None:
            cookie_headers = [{"sessionId": "945112ee160e69a1"}]
        self._all_cookie_headers = tuple(
            "; ".join(
                f"{name}{sep}{value}"
                for name, value in cookie_header.items())
            for cookie_header in cookie_headers
        )

    def get_all(self, header, failobj=None):
        assert header.lower() == "cookie"
        return self._all_cookie_headers


class MockRequestHandler(RequestHandler):
    def __init__(self, *args, **kwargs):
        self.headers = MockHeaders(*args, **kwargs)


def test_get_cookie():
    h = MockRequestHandler()
    assert h.get_cookie("sessionId") == "945112ee160e69a1"


@pytest.mark.parametrize(
    "cookie_name",
    ("sossionId", "sessionid", "session_id", "sessionId2",
     ))
def test_get_wrong_name_1(cookie_name):
    h = MockRequestHandler()
    assert h.get_cookie(cookie_name) is None


@pytest.mark.parametrize(
    "cookie_name",
    ("sossionId", "sessionid", "session_id", "sessionId2",
     ))
def test_get_wrong_name_2(cookie_name):
    h = MockRequestHandler([{cookie_name: "945112ee160e69a1"}])
    assert h.get_cookie("sessionId") is None


@pytest.mark.parametrize(
    "cookies",
    (({"decoy": "yes", "sessionId": "945112ee160e69a1", "other": 4},
      {"sessionId": "f6c34f73c5da37cf", "other": 4},
      ),
     ({"decoy": "yes", "sessionI": "3d8a92a708a334c1", "other": 4},
      {"sessionid": "80367b85a67954fa"},
      {"SESSIONID": "a98d0c0d64a8f7c1"},
      {"sessionId": "945112ee160e69a1"},
      {"sessionId": "f6c34f73c5da37cf", "other": 4},
      ),
     ))
def test_multiple_cookie_headers(cookies):
    h = MockRequestHandler(cookies)
    assert h.get_cookie("sessionId") == "945112ee160e69a1"


def test_bad_cookie_header():
    h = MockRequestHandler(sep="_")
    with pytest.raises(HTTPError) as excinfo:
        _ = h.get_cookie("sessionId")
    assert excinfo.value.status is HTTPStatus.BAD_REQUEST
