import json
import os

from http.cookiejar import DefaultCookiePolicy

import pytest
import requests

from hive.common.socketserver import serving
from hive.common.testing import test_config_dir  # noqa: F401
from hive.common.units import SECONDS
from hive.messaging import Message
from hive.vane_webui_api.server import HTTPServer


class MockValkey:
    def __init__(self):
        self._db = {}

    @staticmethod
    def _encode(value):
        if isinstance(value, str):
            value = value.encode("utf-8")
        assert isinstance(value, bytes)
        return value

    def get(self, key):
        key = self._encode(key)
        value = self._db.get(key, None)
        print(f"GET {key!r} => {value!r}")
        return value

    def mget(self, *keys):
        keys = tuple(self._encode(key) for key in keys)
        values = tuple(self._db.get(key, None) for key in keys)
        print(f"MGET {keys!r} => {values!r}")
        return values

    def set(self, key, value, nx=False, ex=None, px=None, exat=None):
        key = self._encode(key)
        if nx and key in self._db:
            raise NotImplementedError
        value = self._encode(value)
        self._db[key] = value
        print(f"SET {key!r} <= {value!r}")
        return 1

    _unset = object()

    def delete(self, key):
        key = self._encode(key)
        value = self._db.pop(key, self._unset)
        return bool(value is not self._unset)

    def zadd(self, key, values):
        key = self._encode(key)
        zset = self._db.get(key, self._unset)
        if zset is self._unset:
            self._db[key] = zset = []
        for value, score in values.items():
            zset.append((score, self._encode(value)))
        return len(values)

    def zrange(self, key, start, limit, desc=False):
        assert start == 0
        assert limit == 19
        assert desc
        zset = self._db.get(self._encode(key), ())
        return [value for _, value in sorted(zset)]


class MockConnection:
    def add_callback_threadsafe(self, callback):
        callback()  # yolo


class MockProperties:
    content_type = "application/json"


class MockChannel:
    def __init__(self):
        self.connection = MockConnection()
        self._consume_events = {}

    def consume_events(self, *, queue, on_message_callback):
        assert queue not in self._consume_events
        self._consume_events[queue] = on_message_callback

    def publish_event(self, *, message, routing_key):
        self._consume_events[routing_key](
            channel=self,
            message=Message(
                method=None,
                properties=MockProperties(),
                body=json.dumps(message).encode("utf-8"),
            ),
        )


@pytest.fixture
def mock_channel():
    return MockChannel()


@pytest.fixture
def mock_server(test_credentials, mock_channel):
    server = HTTPServer(
        ("127.0.0.1", 0),
        channel=mock_channel,
        bind_and_activate=False,
    )
    server._valkey = MockValkey()
    return server


@pytest.fixture
def mock_valkey(mock_server):
    return mock_server._valkey._db


@pytest.fixture
def valid_csrf(mock_server):
    return mock_server.get_login_token(("mock_client",))


@pytest.fixture
def test_credentials(test_config_dir):  # noqa: F811
    filename = os.path.join(test_config_dir, "vane-webui.json")
    with open(filename, "w") as fp:
        json.dump({
            "username": "valid_username",
            "password_salt": "https://www.youtube.com/watch?v=_o0dn474Dmw",
            "password_hash": "9dd3f24e4824295e3d2bf53329a9c78"
            "8b5dc83ee1f10e448011d676519b446b3",  # "valid_password"
        }, fp)


@pytest.fixture
def test_server(mock_server):
    server = mock_server
    try:
        server.server_bind()
        server.server_activate()
    except BaseException:
        server.server_close()
        raise
    with serving(server):
        host, port = server.server_address
        server.api_url = f"http://{host}:{port}"
        yield server


def _return_ok_secure(self, cookie, request):
    if not cookie.secure:
        return True
    if request.host.startswith("127.0.0.1:"):
        return True
    return DefaultCookiePolicy.return_ok_secure(self, cookie, request)


class HTTPSession(requests.Session):
    def send(self, request, **kwargs):
        if not kwargs.get("timeout"):
            kwargs["timeout"] = 30 * SECONDS
        return super().send(request, **kwargs)


@pytest.fixture
def http_session(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(
            DefaultCookiePolicy,
            "return_ok_secure",
            _return_ok_secure,
        )
        with HTTPSession() as s:
            yield s
