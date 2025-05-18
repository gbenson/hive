import httpx
import pytest

from hive.common import read_config

from . import monkeypatch_httpx  # noqa: F401


@pytest.fixture(scope="module")
def auth() -> httpx.BasicAuth:
    c = read_config("mediawiki-test-credentials")
    return httpx.BasicAuth(
        username=c["username"],
        password=c["password"],
    )
