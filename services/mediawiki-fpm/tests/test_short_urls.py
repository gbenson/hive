import httpx
import pytest

from . import assert_moved_permanently, assert_not_authorized


def test_unterminated_root_redirect(short_url_prefix: str) -> None:
    """Short URL prefix without a trailing slash redirects to add the slash.
    """
    r = httpx.get(short_url_prefix)
    assert_moved_permanently(r, f"{short_url_prefix}/")


@pytest.mark.parametrize(
    "path",
    ("/",
     "/Entrance",
     "/Entrance?ok",
     "/Entrance?ok=1",
     "/NotExist"),
)
def test_unauthenticated(short_url_prefix: str, path: str) -> None:
    """Unauthenticated short URL requests ask for authentication.
    """
    r = httpx.get(f"{short_url_prefix}{path}")
    assert_not_authorized(r)


@pytest.mark.xfail(reason="MediaWiki not configured")  # XXX
def test_root_redirect(
        short_url_prefix: str,
        main_page_short_url: str,
        auth: httpx.BasicAuth,
) -> None:
    """The root of the short URL namespace redirects to main page.
    """
    r = httpx.get(f"{short_url_prefix}/", auth=auth)
    assert_moved_permanently(r, main_page_short_url)


def test_main_page(main_page_short_url: str, auth: httpx.BasicAuth) -> None:
    """The main page is served as expected from its short URL.
    """
    r = httpx.get(main_page_short_url, auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert "LocalSettings.php not found" in r.text  # XXX
