import logging

import httpx

from httpx import _api  # noqa: F401
from httpx import Client, Response

logger = logging.getLogger(__name__)


class MonkeypatchedClient(Client):
    def __init__(self, **kwargs):
        if "http2" not in kwargs:
            kwargs["http2"] = True
        super().__init__(**kwargs)

    def request(self, *args, **kwargs) -> Response:
        response = super().request(*args, **kwargs)
        assert_minimum_security_requirements_met(response)
        return response


httpx.Client = MonkeypatchedClient
httpx._api.Client = MonkeypatchedClient  # for get, post, ...etc


def assert_minimum_security_requirements_met(r: Response) -> None:
    """Every response must meet these basic requirements.
    """
    assert r.http_version == "HTTP/2"

    # https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security
    assert r.headers["strict-transport-security"] == \
        "max-age=63072000; includeSubDomains; preload"

    # https://owasp.org/www-community/attacks/Clickjacking
    assert r.headers["content-security-policy"] == "frame-ancestors 'none'"
    assert r.headers["x-frame-options"] == "DENY"

    # Stealth
    assert r.headers["referrer-policy"] == "no-referrer"
    assert r.headers["server"] == "nginx"
    assert "x-powered-by" not in r.headers, r.headers["x-powered-by"]

    logger.info("Minimum security requirements met")
