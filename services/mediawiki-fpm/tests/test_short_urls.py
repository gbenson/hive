import httpx
import pytest

from .config import SHORT_URL_PREFIX
from .util import assert_moved_permanently, assert_not_authorized


def test_unterminated_root_redirect() -> None:
    """Short URL prefix without a trailing slash redirects to add the slash.
    """
    r = httpx.get(SHORT_URL_PREFIX)
    assert_moved_permanently(r, f"{SHORT_URL_PREFIX}/")


@pytest.mark.parametrize(
    "path",
    ("/",
     "/Entrance",
     "/Entrance?ok",
     "/Entrance?ok=1",
     "/NotExist"),
)
def test_unauthenticated(path: str) -> None:
    """Unauthenticated short URL requests ask for authentication.
    """
    r = httpx.get(f"{SHORT_URL_PREFIX}{path}")
    assert_not_authorized(r)


def test_root_redirect(auth: httpx.BasicAuth) -> None:
    """The root of the short URL namespace redirects to main page.
    """
    # XXX it would it you were logged in to the wiki!
    r = httpx.get(f"{SHORT_URL_PREFIX}/", auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert "<title>Login required - Hive</title>" in r.text


def test_main_page(auth: httpx.BasicAuth) -> None:
    """The main page is served as expected from its short URL.
    """
    # XXX it would it you were logged in to the wiki!
    r = httpx.get(f"{SHORT_URL_PREFIX}/Entrance", auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert "<title>Login required - Hive</title>" in r.text
