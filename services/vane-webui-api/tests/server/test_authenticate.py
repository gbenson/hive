import json

from enum import IntEnum

import pytest

from hive.vane_webui_api.exceptions import HTTPError
from hive.vane_webui_api.request_handler import RequestHandler


class Outcome(IntEnum):
    CSRF_TOKEN_SENT = 601


class MockRequestHandler(RequestHandler):
    @classmethod
    def run_test(cls, *args, **kwargs):
        handler = cls(*args, **kwargs)
        with pytest.raises(HTTPError) as excinfo:
            handler.route_api_request()
        return excinfo.value.status

    def send_response(self, status, *args):
        raise HTTPError(status)

    def send_csrf_token(self):
        self.send_response(Outcome.CSRF_TOKEN_SENT)

    def __init__(self, server, json_payload):
        self.server = server
        self.command = "POST"
        self.path = "/login"
        self.headers = type("MockHeaders", (), {"items": lambda: ()})
        self.__payload = json.dumps(json_payload)

    def read_json_payload(self):
        return json.loads(self.__payload)


@pytest.fixture
def valid_payload(test_credentials, valid_csrf):  # noqa: F821
    return {
        "user": "valid_username",
        "pass": "valid_password",
        "csrf": valid_csrf,
    }


def test_valid_credentials(valid_payload, mock_server):
    """Login is successful with valid credentials.
    """
    payload = valid_payload
    result = MockRequestHandler.run_test(mock_server, payload)
    assert result == 204


@pytest.mark.parametrize("knockout", ("user", "pass", "csrf"))
def test_missing_field(valid_payload, mock_server, knockout):
    """Login with any field missing returns a CSRF token.
    """
    payload = valid_payload
    _ = payload.pop(knockout)
    result = MockRequestHandler.run_test(mock_server, payload)
    assert result == Outcome.CSRF_TOKEN_SENT


@pytest.mark.parametrize("invalidate", ("user", "pass", "csrf"))
def test_invalid_field(valid_payload, mock_server, invalidate):
    """Login with any field invalid returns a CSRF token.
    """
    payload = valid_payload
    payload[invalidate] += "x"
    result = MockRequestHandler.run_test(mock_server, payload)
    assert result == Outcome.CSRF_TOKEN_SENT


@pytest.mark.parametrize("invalidate", ("user", "pass", "csrf"))
def test_mistyped_field(valid_payload, mock_server, invalidate):
    """Login with any field the wrong type returns a CSRF token.
    """
    payload = valid_payload
    payload[invalidate] = 4
    result = MockRequestHandler.run_test(mock_server, payload)
    assert result == Outcome.CSRF_TOKEN_SENT
