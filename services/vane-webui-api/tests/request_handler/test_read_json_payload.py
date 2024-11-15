import json

from io import BytesIO
from http.client import HTTPMessage

import pytest

from hive.vane_webui_api.exceptions import HTTPError
from hive.vane_webui_api.request_handler import RequestHandler


class MockRequestHandler(RequestHandler):
    def __init__(self):
        self.command = "POST"
        self.headers = HTTPMessage()
        self.headers["content-type"] = "application/json"
        payload = json.dumps(dict(hello="world")).encode()
        self.headers["content-length"] = f"{len(payload)}"
        self.rfile = BytesIO(payload)


@pytest.fixture
def handler():
    return MockRequestHandler()


def test_setup(handler):
    assert handler.read_json_payload() == {"hello": "world"}


def test_bad_request_method(handler):
    handler.command = "GET"
    with pytest.raises(ValueError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.args == ("GET",)


def test_no_content_type(handler):
    del handler.headers["content-type"]
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 415  # Unsupported Media Type


def test_bad_content_type(handler):
    del handler.headers["content-type"]
    handler.headers["content-type"] = "text/plain"
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 415  # Unsupported Media Type


def test_no_content_length(handler):
    del handler.headers["content-length"]
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 411  # Length Required


@pytest.mark.parametrize("content_length", ("0", 0, None, False))
def test_zero_content_length(handler, content_length):
    del handler.headers["content-length"]
    handler.headers["content-length"] = content_length
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 411  # Length Required


@pytest.mark.parametrize("content_length", ("-1", "a", "01", "0.1", "0x16"))
def test_bad_content_length(handler, content_length):
    del handler.headers["content-length"]
    handler.headers["content-length"] = content_length
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 400  # Bad Request


def test_content_too_large(handler):
    del handler.headers["content-length"]
    handler.headers["content-length"] = "1025"
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 413  # Content Too Large


def test_payload_too_short(handler):
    handler.rfile.read(1)
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 400  # Bad Request


def test_corrupt_payload(handler):
    handler.rfile.write(b"x")
    handler.rfile.seek(0)
    with pytest.raises(HTTPError) as excinfo:
        handler.read_json_payload()
    assert excinfo.value.status == 400  # Bad Request
