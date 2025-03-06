import json

from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from hive.common import httpx
from hive.common.socketserver import serving


class TestServerRequestHandler(BaseHTTPRequestHandler):
    __test__ = False

    def do_GET(self):
        response = json.dumps({
            "requestline": self.requestline,
            "headers": dict(
                (key.lower(), value)
                for key, value in self.headers.items()
            ),
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


@pytest.fixture(scope="module")
def test_server():
    server = HTTPServer(("127.0.0.1", 0), TestServerRequestHandler)
    with serving(server):
        host, port = server.server_address
        server.base_url = f"http://{host}:{port}"
        yield server


def test_get(test_server):
    r = httpx.get(f"{test_server.base_url}/hello-world")
    r.raise_for_status()
    req = r.json()
    assert req["requestline"].startswith("GET /hello-world HTTP/1.")
    assert req["headers"]["host"] == ("%s:%d" % test_server.server_address)
    user_agent = req["headers"]["user-agent"]
    assert user_agent.startswith("HiveBot/0.")
    assert " (bot; +https://" in user_agent


def test_response_as_json(test_server):
    r = httpx.get(test_server.base_url)
    r.raise_for_status()
    res = httpx.response_as_json(r)
    assert res.keys() == {
        "body",
        "headers",
        "http_version",
        "reason_phrase",
        "status_code",
        "url",
    }
    assert res["url"] == test_server.base_url
    assert res["http_version"].startswith("HTTP/1.")
    assert res["status_code"] == 200
    assert res["reason_phrase"] == "OK"
    assert json.loads(res["body"]) == r.json()
    headers = dict(res["headers"])
    assert headers.keys() == {
        "content-length",
        "content-type",
        "date",
        "server",
    }
    assert headers["content-type"] == "application/json"
    assert headers["content-length"] == str(len(r.content))
