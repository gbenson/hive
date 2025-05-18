import httpx
import pytest

from .config import UPLOAD_URL_PREFIX
from .util import (
    assert_forbidden,
    assert_moved_permanently,
    assert_not_authorized,
)


def test_unterminated_root_redirect() -> None:
    """Upload URL prefix without a trailing slash redirects to add the slash.
    """
    r = httpx.get(UPLOAD_URL_PREFIX)
    assert_moved_permanently(r, f"{UPLOAD_URL_PREFIX}/")


@pytest.mark.parametrize(
    "path",
    ("/",
     "/not-exist.png",
     ))
def test_unauthenticated(path: str) -> None:
    """Unauthenticated upload URL requests ask for authentication.
    """
    r = httpx.get(f"{UPLOAD_URL_PREFIX}{path}")
    assert_not_authorized(r)


@pytest.mark.parametrize(
    "path",
    ("/",
     "/9/",
     "/9/94/",
     "/archive/",
     "/lockdir/",
     "/lost+found/",
     ))
def test_no_directory_indexes(path: str, auth: httpx.BasicAuth) -> None:
    """Directory indexes are forbidden in the upload URL namespace.
    """
    r = httpx.get(f"{UPLOAD_URL_PREFIX}{path}", auth=auth)
    assert_forbidden(r)


def test_static_uploads(auth: httpx.BasicAuth) -> None:
    """Authenticated upload requests serve as expected.
    """
    path = "/9/94/IMG_20191018_115301652.jpg"
    r = httpx.get(f"{UPLOAD_URL_PREFIX}{path}", auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert r.content.startswith(b"\xff\xd8\xff\xe0\x00\x10JFIF")
