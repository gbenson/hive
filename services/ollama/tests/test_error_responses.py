from dataclasses import asdict, dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from requests import RequestException

from hive.common.socketserver import serving
from hive.ollama import Service


@dataclass
class MockChannel:
    call_log: list = field(default_factory=list)
    consumer_name: str = "mock_consumer"

    def publish_event(self, **kwargs):
        self.call_log.append(("publish_event", kwargs))


class MockMessage1:
    @property
    def correlation_id(self) -> str:
        return f"{type(self).__name__}.correlation_id"


def test_error_response_1():
    service = Service()
    channel = MockChannel()
    with pytest.raises(AttributeError):
        service.on_request(channel, MockMessage1())
    assert channel.call_log == [(
        "publish_event", {
            "correlation_id": "MockMessage1.correlation_id",
            "message": {
                "error": "AttributeError: 'MockMessage1' object has no attribute 'json'",
                "done": True,
            },
            "routing_key": "ollama.api.responses",
        },
    )]


@dataclass
class MockMessage(MockMessage1):
    method: str = "POST"
    request_uri: str = "/api/chat"

    def json(self):
        return asdict(self)


@dataclass
class MockMessage2(MockMessage):
    request_uri: str = "http://169.254.169.254/latest/meta-data/iam/credentials"


def test_error_response_2():
    service = Service()
    channel = MockChannel()
    with pytest.raises(ValueError):
        service.on_request(channel, MockMessage2())
    assert channel.call_log == [(
        "publish_event", {
            "correlation_id": "MockMessage2.correlation_id",
            "message": {
                "error": "ValueError: http://169.254.169.254/latest/meta-data/iam/credentials",
                "done": True,
            },
            "routing_key": "ollama.api.responses",
        },
    )]


@dataclass
class MockMessage3(MockMessage):
    method: str = "OPTIONS"


def test_error_response_3():
    service = Service()
    channel = MockChannel()
    with pytest.raises(NotImplementedError):
        service.on_request(channel, MockMessage3())
    assert channel.call_log == [(
        "publish_event", {
            "correlation_id": "MockMessage3.correlation_id",
            "message": {
                "error": "NotImplementedError: OPTIONS",
                "done": True,
            },
            "routing_key": "ollama.api.responses",
        },
    )]


class MockMessage4(MockMessage):
    pass


def test_error_response_4():
    service = Service()
    channel = MockChannel()
    with pytest.raises(KeyError):
        service.on_request(channel, MockMessage4())
    assert channel.call_log == [(
        "publish_event", {
            "correlation_id": "MockMessage4.correlation_id",
            "message": {
                "error": "KeyError: 'data'",
                "done": True,
            },
            "routing_key": "ollama.api.responses",
        },
    )]


@dataclass
class MockMessage5(MockMessage):
    data: dict = field(default_factory=dict)


def test_error_response_5():
    service = Service()
    service.ollama_api_url = "http://127.0.0.1:9"
    channel = MockChannel()
    with pytest.raises(RequestException):
        service.on_request(channel, MockMessage5())
    message = channel.call_log[1][1]["message"]["error"]
    assert message.startswith("ConnectionError: ")
    assert channel.call_log == [(
        "publish_event", {
            "correlation_id": "MockMessage5.correlation_id",
            "message": {
                "hive_flow": {
                    "consumer": "mock_consumer",
                    "status": "generating response",
                },
                "done": False,
            },
            "routing_key": "ollama.api.responses",
        },
    ), (
        "publish_event", {
            "correlation_id": "MockMessage5.correlation_id",
            "message": {
                "error": message,
                "done": True,
            },
            "routing_key": "ollama.api.responses",
        },
    )]


class MockMessage6(MockMessage5):
    pass


def test_error_response_6(test_server):
    service = Service()
    service.ollama_api_url = test_server.base_url
    channel = MockChannel()
    with pytest.raises(RequestException):
        service.on_request(channel, MockMessage6())
    message = channel.call_log[1][1]["message"]["error"]
    assert message.startswith("HTTPError: 501 Server Error: Unsupported method ('POST') ")
    assert channel.call_log == [(
        "publish_event", {
            "correlation_id": "MockMessage6.correlation_id",
            "message": {
                "hive_flow": {
                    "consumer": "mock_consumer",
                    "status": "generating response",
                },
                "done": False,
            },
            "routing_key": "ollama.api.responses",
        },
    ), (
        "publish_event", {
            "correlation_id": "MockMessage6.correlation_id",
            "message": {
                "error": message,
                "done": True,
            },
            "routing_key": "ollama.api.responses",
        },
    )]


@pytest.fixture(scope="module")
def test_server():
    server = HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    with serving(server):
        host, port = server.server_address
        server.base_url = f"http://{host}:{port}"
        yield server
