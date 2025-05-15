from typing import Callable, TypeAlias

import httpx
import pytest

from hive.common import read_config

from . import monkeypatch_httpx  # noqa: F401

URLRewriter: TypeAlias = Callable[[str], str]


@pytest.fixture(scope="module")
def hostnames() -> dict[str, str]:
    return read_config("hostnames")


@pytest.fixture(scope="module")
def default_hostname(hostnames: dict[str, str]) -> str:
    return hostnames["DEFAULT_HOSTNAME"]


@pytest.fixture(scope="module")
def service_hostname(hostnames: dict[str, str]) -> str:
    return hostnames["SERVICE_HOSTNAME"]


@pytest.fixture(scope="module")
def with_default_hostname(
        default_hostname: str,
        service_hostname: str,
) -> URLRewriter:
    default_prefix = f"https://{default_hostname}/"
    service_prefix = f"https://{service_hostname}/"

    def rewrite(url: str) -> str:
        if url.startswith(service_prefix):
            return f"{default_prefix}{url[len(service_prefix):]}"
        if url == service_prefix[:-1]:
            return default_prefix[:-1]
        raise ValueError(url)

    return rewrite


@pytest.fixture(scope="module")
def mediawiki_paths() -> dict[str, str]:
    return read_config("mediawiki-paths")


@pytest.fixture(scope="module")
def auth() -> httpx.BasicAuth:
    c = read_config("mediawiki-test-credentials")
    return httpx.BasicAuth(
        username=c["username"],
        password=c["password"],
    )


@pytest.fixture(scope="module")
def article_path(mediawiki_paths: dict[str, str]) -> str:
    """The path used to construct short URL prefixes.

    For English Wikipedia this would be "wiki", to yield URLs of the
    form <https://en.wikipedia.org/wiki/Amalia_Ulman>.
    """
    result = mediawiki_paths["WG_ARTICLE_PATH"]
    assert result.strip("/") == result  # no leading or trailing slash
    return result


@pytest.fixture(scope="module")
def short_url_prefix(service_hostname: str, article_path: str) -> str:
    """The short URL prefix of the site.

    For English Wikipedia this would be "https://en.wikipedia.org/wiki".
    """
    return f"https://{service_hostname}/{article_path}"


@pytest.fixture(scope="module")
def script_path(mediawiki_paths: dict[str, str]) -> str:
    """ The URL base path to the directory containing the wiki.

    For English Wikipedia this would be "w", to yield URLs of the
    form <https://en.wikipedia.org/w/index.php?title=Amalia_Ulman>.
    """
    result = mediawiki_paths["WG_SCRIPT_PATH"]
    assert result.strip("/") == result  # no leading or trailing slash
    return result


@pytest.fixture(scope="module")
def script_url_prefix(service_hostname: str, script_path: str) -> str:
    """The URL prefix of the directory containing the wiki.

    For English Wikipedia this would be "https://en.wikipedia.org/w".
    """
    return f"https://{service_hostname}/{script_path}"


@pytest.fixture(scope="module")
def main_page_short_url(short_url_prefix: str) -> str:
    """https://en.wikipedia.org/wiki/Amalia_Ulman
    """
    return f"{short_url_prefix}/Entrance"


@pytest.fixture(scope="module")
def main_page_script_url(script_url_prefix: str) -> str:
    """https://en.wikipedia.org/w/index.php?title=Amalia_Ulman
    """
    return f"{script_url_prefix}/index.php?title=Entrance"
