from http import HTTPStatus
from itertools import chain

import pytest

from hive.vane_webui_api.request_handler import RequestHandler


class MockRequestHandler(RequestHandler):
    @classmethod
    def run_test(cls, **kwargs):
        handler = cls(**kwargs)
        getattr(handler, f"do_{handler.command}")()
        return handler._record

    def __init__(self, *, method="GET", **kwargs):
        self.command = method
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self._record = []

    @property
    def do_WOW(self):
        return self.do_GET

    def send_error(self, *args, **kwargs):
        self._record.append(("send_error", args, kwargs))

    def get_cookie(self, *args, **kwargs):
        self._record.append(("get_cookie", args, kwargs))


def test_internal_server_error():
    """Unhandled errors result in 500 Internal Server Error.
    """
    record = MockRequestHandler.run_test()
    assert record == [("send_error", (HTTPStatus.INTERNAL_SERVER_ERROR,), {})]


@pytest.mark.parametrize(
    "path",
    (None, "", "/", "", "/", "/ap/login", "/logi",
     "?login", "_login",
     "/?login", "/_login",
     "/login/", "/logine", "/LOGIN",
     "/login?hello", "/log in", "/login ", "/api/login",
     ))
def test_route_not_found(path):
    """Non-existent routes result in 404 Not Found.
    """
    record = MockRequestHandler.run_test(path=path)
    assert record == [("send_error", (HTTPStatus.NOT_FOUND,), {})]


@pytest.mark.parametrize(
    "method_path",
    chain.from_iterable(
        (f"{method} /{route}"
         for method in methods)
        for route, methods in {
                "chat": ("GET", "HEAD", "WOW"),
                "events": ("POST", "WOW"),
                "login": ("WOW",),
        }.items()
    ))
def test_method_not_allowed(method_path):
    """Non-allowed methods result in 405 Method Not Allowed.
    """
    method, path = method_path.split()
    record = MockRequestHandler.run_test(method=method, path=path)
    assert record == [("send_error", (HTTPStatus.METHOD_NOT_ALLOWED,), {})]


@pytest.mark.parametrize(
    "method_path",
    ("POST /chat",
     "GET /events",
     ))
def test_unauthorized(method_path):
    """Unauthenticated requests to routes except login yield 401 Unauthorized.
    """
    method, path = method_path.split()
    record = MockRequestHandler.run_test(
        method=method,
        path=path,
        request_version="HTTP/1.1",
    )
    assert record == [
        ("get_cookie", ("sessionId",), {}),
        ("send_error", (HTTPStatus.UNAUTHORIZED,), {}),
    ]
