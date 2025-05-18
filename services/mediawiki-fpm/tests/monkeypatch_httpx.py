import logging

from urllib.parse import urlparse

import httpx

from httpx import _api  # noqa: F401
from httpx import BasicAuth, Client, Response, URL

from . import config

from .config import DEFAULT_HOSTNAME, SERVICE_HOSTNAME
from .util import assert_not_authorized, assert_not_found

logger = logging.getLogger(__name__)


class MonkeypatchedClient(Client):
    def __init__(self, **kwargs):
        if "http2" not in kwargs:
            kwargs["http2"] = True
        super().__init__(**kwargs)

    def request(
            self,
            method: str,
            url: URL | str,
            *,
            auth: BasicAuth | None = None,
            **kwargs,
    ) -> Response:
        hostname = urlparse(url).hostname

        # For every request made with HTTP authentication, check
        # the same request without authentication returns a 401.
        if auth is not None:
            logger.info("Checking without authentication")
            match hostname:
                case config.SERVICE_HOSTNAME:
                    self._assert_not_authorized(method, url, **kwargs)
                case config.DEFAULT_HOSTNAME:
                    self._assert_not_found(method, url, **kwargs)
                case _:
                    raise NotImplementedError(url)

        # For every request made to the service hostname, check
        # the same request to the default hostname returns a 404.
        if hostname == SERVICE_HOSTNAME:
            logger.info("Checking the default hostname")
            stem = url.removeprefix(f"https://{SERVICE_HOSTNAME}/")
            assert stem != url
            self._assert_not_found(
                method,
                f"https://{DEFAULT_HOSTNAME}/{stem}",
                auth=auth,
                **kwargs,
            )

        response = super().request(method, url, auth=auth, **kwargs)
        assert_minimum_security_requirements_met(response)
        return response

    def _assert_not_authorized(
            self,
            method: str,
            url: URL | str,
            **kwargs,
    ) -> None:
        r = httpx.request(method, url, **kwargs)
        assert_not_authorized(r)

    def _assert_not_found(self, *args, **kwargs) -> None:
        r = httpx.request(*args, **kwargs)
        assert_not_found(r)


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
