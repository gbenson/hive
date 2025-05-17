import httpx
import pytest

from . import assert_moved_permanently, assert_not_authorized, assert_forbidden


def test_unterminated_root_redirect(resource_url_prefix: str) -> None:
    """Resource URL prefix without a trailing slash redirects to add the slash.
    """
    r = httpx.get(resource_url_prefix)
    assert_moved_permanently(r, f"{resource_url_prefix}/")


@pytest.mark.parametrize(
    "path",
    ("/",
     "/hive/apple-touch-icon.png",
     "/resources/assets/poweredby_mediawiki_176x62.png",
     "/not-existing-resource.png",
     "/resources/"),
)
def test_unauthenticated(resource_url_prefix: str, path: str) -> None:
    """Unauthenticated resource URL requests ask for authentication.
    """
    r = httpx.get(f"{resource_url_prefix}{path}")
    assert_not_authorized(r)


@pytest.mark.parametrize(
    "path",
    ("/",
     "/hive/",
     "/resources/",
     "/resources/assets/"),
)
def test_no_directory_indexes(
        resource_url_prefix: str,
        path: str,
        auth: httpx.BasicAuth,
) -> None:
    """Directory indexes are forbidden in the resource URL namespace.
    """
    r = httpx.get(f"{resource_url_prefix}{path}", auth=auth)
    assert_forbidden(r)


@pytest.mark.parametrize(
    "path",
    ("/hive/apple-touch-icon.png",
     "/resources/assets/poweredby_mediawiki_176x62.png"),
)
def test_static_resources(
        resource_url_prefix: str,
        path: str,
        auth: httpx.BasicAuth,
) -> None:
    """Authenticated static resource requests serve as expected.
    """
    r = httpx.get(f"{resource_url_prefix}{path}", auth=auth)

    assert r.status_code == httpx.codes.OK
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert r.content.startswith(b"\x89PNG\r\n\x1a\n")
