import httpx
import pytest

from .config import SCRIPT_URL_PREFIX
from .util import assert_moved_permanently, assert_not_authorized


def test_unterminated_root_redirect() -> None:
    """Script URL prefix without a trailing slash redirects to add the slash.
    """
    r = httpx.get(SCRIPT_URL_PREFIX)
    assert_moved_permanently(r, f"{SCRIPT_URL_PREFIX}/")


@pytest.mark.parametrize(
    "path",
    ("/",
     "/indox.php?title=Entrance",
     "/index.php?title=Entronce",
     "/index.php?totle=Entrance",
     "/index.php?title=Special:MovePage",
     "/notexist.php",
     "/notexist.php?",
     "/notexist.php?title=Entrance",
     ))
def test_unauthenticated(path: str) -> None:
    """Unauthenticated script URL requests ask for authentication.
    """
    r = httpx.get(f"{SCRIPT_URL_PREFIX}{path}")
    assert_not_authorized(r)


def test_root_redirect(auth: httpx.BasicAuth) -> None:
    """The root of the script URL namespace redirects to main page.
    """
    # XXX it would it you were logged in!
    r = httpx.get(f"{SCRIPT_URL_PREFIX}/", auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert "<title>Login required - Hive</title>" in r.text


@pytest.mark.parametrize(
    "path",
    ("/index.php",
     "/index.php?",
     "/index.php?title",
     "/index.php?title=",
     "/index.php?title=Entrance",
     ))
def test_main_page(path: str, auth: httpx.BasicAuth) -> None:
    """The main page is served as expected from its script URL.
    """
    # XXX it would it you were logged in to the wiki!
    r = httpx.get(f"{SCRIPT_URL_PREFIX}{path}", auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert "<title>Login required - Hive</title>" in r.text
