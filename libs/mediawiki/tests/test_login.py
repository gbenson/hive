import json
import logging
import os

import pytest

from mediawiki import mediawiki as mediawiki_module

from hive.common.testing import test_config_dir  # noqa: F401
from hive.mediawiki import HiveWiki


def test_login(test_config, mock_requests, caplog):
    auth_headers = {
        "Authorization": "Basic aHR0cC11c2VybmFtZTpodHRwLXBhc3N3b3Jk",
    }
    csrf_token = "9ed1499d99c0c34c73faa07157b3b6075b427365+\\"
    mock_requests.expect(
        MockRequest(
            method="GET",
            url="https://hive.host/path/to/api",
            headers=auth_headers,
            params={
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json"
            },
        ),
        MockResponse(
            json={
                "batchcomplete": "",
                "query": {
                    "tokens": {
                        "logintoken": csrf_token,
                    },
                },
            },
        ))
    mock_requests.expect(
        MockRequest(
            method="POST",
            url="https://hive.host/path/to/api",
            headers=auth_headers,
            data={
                "action": "login",
                "lgname": "wiki-username",
                "lgpassword": "wiki-password",
                "lgtoken": csrf_token,
                "format": "json"
            },
        ),
        MockResponse(
            json={
                "login": {
                    "lguserid": 21,
                    "result": "Success",
                    "lgusername": "William"
                }
            },
        ))
    mock_requests.expect(
        MockRequest(
            method="GET",
            url="https://hive.host/path/to/api",
            headers=auth_headers,
            params={
                "action": "query",
                "meta": "siteinfo",
                "siprop": "extensions|general",
                "format": "json"
            },
        ),
        MockResponse(
            json={
                "query": {
                    "general": {
                        "generator": "MediaWiki 1.35.10",
                        "server": "https://hive.host",
                    },
                    "extensions": [
                        {"name": name}
                        for name in [
                                "MinervaNeue", "Vector", "Cite",
                                "Scribunto", "TemplateStyles",
                                "ParserFunctions", "SyntaxHighlight",
                                "Interwiki", "MobileFrontend",
                        ]
                    ],
                },
            },
        ))

    with caplog.at_level(logging.DEBUG):
        wiki = HiveWiki()
    assert wiki.logged_in
    assert wiki.api_version == "1.35.10"
    assert wiki.base_url == "https://hive.host"
    assert wiki.extensions == [
        "Cite", "Interwiki", "MinervaNeue", "MobileFrontend",
        "ParserFunctions", "Scribunto", "SyntaxHighlight",
        "TemplateStyles", "Vector"]


@pytest.fixture
def test_config(test_config_dir):  # noqa: F811
    filename = os.path.join(test_config_dir, "mediawiki.json")
    config = {
        "url": "https://hive.host/path/to/api",
        "http_auth": {
            "username": "http-username",
            "password": "http-password",
        },
        "username": "wiki-username",
        "password": "wiki-password",
    }
    with open(filename, "w") as fp:
        json.dump({"mediawiki": config}, fp)
    yield config


@pytest.fixture
def mock_requests(monkeypatch):
    module = MockRequests()
    with monkeypatch.context() as m:
        m.setattr(mediawiki_module, "requests", module)
        yield module
    assert not module._expectations


class MockRequests:
    def __init__(self):
        self._expectations = []

    def expect(self, want_request, mock_response):
        self._expectations.append((want_request, mock_response))

    def Session(self):
        return MockSession(self._expectations)


class MockSession:
    def __init__(self, expectations):
        self._expectations = expectations
        self.headers = {}
        self.auth = None
        self._is_open = True

    def close(self):
        assert self._is_open
        self._is_open = False

    def get(self, *args, **kwargs):
        return self._handle("GET", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._handle("POST", *args, **kwargs)

    def _handle(self, *args, **kwargs):
        assert self._is_open

        got_request = MockRequest(*args, **kwargs)
        if self.auth:
            got_request = self.auth(got_request)

        timeout = got_request.timeout
        assert timeout
        assert timeout > 0
        assert timeout < 300

        want_request, mock_response = self._expectations.pop(0)
        assert got_request == want_request
        return mock_response


class MockRequest:
    def __init__(self, method, url, timeout=None, headers=None, **kwargs):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self.kwargs = kwargs

    def __eq__(self, other):
        return not (self != other)

    def __ne__(self, other):
        for attr in ("method", "url", "headers", "kwargs"):
            a, b = (getattr(ob, attr) for ob in (self, other))
            if a == b:
                continue
            print(f"{attr}: {a!r} != {b!r}")
            return True
        return False


class MockResponse:
    def __init__(self, json):
        self._json = json

    def json(self):
        return self._json

    @property
    def status_code(self):
        return 200
