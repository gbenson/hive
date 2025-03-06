from __future__ import annotations

import weakref

from datetime import timedelta
from typing import Any, Callable, Optional

from mediawiki import (
    MediaWiki as PyMediaWiki,
    MediaWikiPage as PyMediaWikiPage,
)
from requests import PreparedRequest
from requests.auth import AuthBase, HTTPBasicAuth

from hive.common import read_config
from hive.common.units import MINUTE, SECOND

from .__version__ import __version__

__url__ = "https://github.com/gbenson/hive"


class HiveWiki(PyMediaWiki):
    DEFAULT_CONFIG_KEY = "mediawiki"
    MAX_REQUEST_TIMEOUT = 10 * MINUTE
    MIN_REQUEST_INTERVAL = 0.1 * SECOND

    def __init__(self, **kwargs):
        config_sect = self.DEFAULT_CONFIG_KEY
        config_key = kwargs.pop("config_key", config_sect)

        if config_key:
            config = read_config(config_key)
            config = config.get(config_sect, {})
            config.update(kwargs)
            kwargs = config

        http_auth = kwargs.pop("http_auth", None)
        if isinstance(http_auth, dict):
            http_auth = HTTPBasicAuth(**http_auth)
        self._http_auth = http_auth

        if "rate_limit" not in kwargs:
            kwargs["rate_limit"] = True
        if "rate_limit_wait" not in kwargs:
            kwargs["rate_limit_wait"] = self.MIN_REQUEST_INTERVAL

        self._need_user_agent = not bool(kwargs.get("user_agent"))
        super().__init__(**kwargs)
        assert not self._need_user_agent

    def _reset_session(self):
        if self._need_user_agent:
            self._need_user_agent = False
            self.user_agent = \
                f"Hivetool/{__version__} ({self.user_agent}; +{__url__})"
            return

        self.__workaround_rate_limit_uninit()
        self._hive_validate_config()
        super()._reset_session()
        session = self._session
        if not (auth := session.auth):
            auth = self._http_auth
        session.auth = HiveAuthenticator(weakref.proxy(self), auth)

    def __workaround_rate_limit_uninit(self):
        """PyMediaWiki 0.7.4 indirectly calls _reset_session()
        before configuring rate limiting."""  # XXX remove
        try:
            _ = self.rate_limit
        except AttributeError:
            self._rate_limit = True
        try:
            _ = self.rate_limit_min_wait
        except AttributeError:
            self._min_wait = self.MIN_REQUEST_INTERVAL

    def _hive_validate_config(self) -> None:
        """Raise a ValueError if the current configuration is unsafe.
        """
        timeout = self.timeout
        if not timeout or timeout < 0 or (
                timeout > self.MAX_REQUEST_TIMEOUT.total_seconds()):
            raise ValueError(f"timeout: {timeout!r}")

        if not self.rate_limit:
            raise ValueError(f"rate_limit: {self.rate_limit!r}")

        interval = self.rate_limit_min_wait
        if interval < self.MIN_REQUEST_INTERVAL:
            raise ValueError(f"rate_limit_min_wait: {interval!r}")

        if not self.verify_ssl:
            raise ValueError(f"verify_ssl: {self.verify_ssl!r}")

    def page(self, *args, **kwargs) -> HiveWikiPage:
        return HiveWikiPage(super().page(*args, **kwargs))


class HiveAuthenticator(AuthBase):
    def __init__(self, wiki, auth=None):
        self._wiki = wiki
        self._auth = auth

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        self._wiki._hive_validate_config()

        if not self._auth:
            return r

        if not r.url.startswith("https://"):
            raise ValueError(r.url)

        session = self._wiki._session
        if not session.verify:
            raise ValueError(f"session.verify: {session.verify!r}")

        return self._auth(r)


class HiveWikiPage:
    def __init__(self, wrapped: PyMediaWikiPage):
        self._hive_wrapped = wrapped

    def __getattr__(self, attr):
        return getattr(self._hive_wrapped, attr)

    def append(self, wikitext: str) -> None:
        # XXX this could race, need to send a revision id or timestamp
        page_wikitext = self.wikitext
        if "\n" not in page_wikitext[len(page_wikitext.rstrip()):]:
            wikitext = f"\n{wikitext.rstrip()}"
        self._append(wikitext)

    def _append(self, wikitext: str) -> None:
        params = {
            "action": "query",
            "meta": "tokens",
            "format": "json",
        }
        resp = self.mediawiki._get_response(params)
        token = resp["query"]["tokens"]["csrftoken"]

        params = {
            "action": "edit",
            "appendtext": wikitext,
            "format": "json",
            "token": token,
        }

        if self.pageid:
            params["pageid"] = self.pageid
        elif self.title:
            params["title"] = self.title

        resp = self.mediawiki._post_response(params)
        self.mediawiki._check_error_response(resp, "append")

        # XXX probably need to invalidate more
        self._hive_wrapped._wikitext = None
