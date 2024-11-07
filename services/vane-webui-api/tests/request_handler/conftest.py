from http.server import HTTPServer
from threading import Lock
from typing import Optional

import pytest

from hive.common.socketserver import serving
from hive.vane_webui_api.request_handler import RequestHandler


class MockServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._csrf_lock = Lock()
        self._csrf_suffix = ""

    @property
    def _csrf_suffix(self) -> str:
        with self._csrf_lock:
            return self.__csrf_suffix

    @_csrf_suffix.setter
    def _csrf_suffix(self, value):
        with self._csrf_lock:
            self.__csrf_suffix = value

    @property
    def url(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}"

    def is_logged_in(self, candidate: str):
        return candidate == "f9e5d8c25951ac8c9d9856e346c437406a1316094bd0b"

    def get_login_token(self, client_address) -> str:
        return f"valid_csrf{self._csrf_suffix}"

    def authenticate(self, creds, request) -> Optional[str]:
        self._csrf_suffix = "_2"
        try:
            username = creds["user"]
            password = creds["pass"]
            csrf = creds["csrf"]
        except KeyError:
            return None
        if (username == "valid_user"
                and password == "valid_pass"
                and csrf == "valid_csrf"):
            return "f9e5d8c25951ac8c9d9856e346c437406a1316094bd0b"
        return None


@pytest.fixture(scope="session")
def mock_server():
    server = MockServer(("127.0.0.1", 0), RequestHandler)
    with serving(server):
        yield server


@pytest.fixture
def login_url(mock_server):
    mock_server._csrf_suffix = ""
    return f"{mock_server.url}/login"
