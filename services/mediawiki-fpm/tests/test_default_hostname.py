import httpx
import pytest

from . import assert_not_found

from .conftest import URLRewriter


def test_unterminated_short_url_root(
        short_url_prefix: str,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(short_url_prefix))
    assert_not_found(r)


def test_unterminated_resource_url_root(
        resource_url_prefix: str,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(resource_url_prefix))
    assert_not_found(r)


@pytest.mark.parametrize(
    "path",
    ("/",
     "/Entrance?ok",
     "/Entrance?ok=1",
     "/NotExist"),
)
def test_unauthenticated_short_url(
        short_url_prefix: str,
        path: str,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(f"{short_url_prefix}{path}"))
    assert_not_found(r)


@pytest.mark.parametrize(
    "path",
    ("/",
     "/hive/apple-touch-icon.png",
     "/resources/assets/poweredby_mediawiki_176x62.png",
     "/not-existing-resource.png",
     "/resources/"),
)
def test_unauthenticated_resource_url(
        resource_url_prefix: str,
        path: str,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(f"{resource_url_prefix}{path}"))
    assert_not_found(r)


def test_short_url_root(
        short_url_prefix: str,
        auth: httpx.BasicAuth,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(f"{short_url_prefix}/"), auth=auth)
    assert_not_found(r)


@pytest.mark.parametrize(
    "path",
    ("/",
     "/hive",
     "/hive/",
     "/resources",
     "/resources/",
     "/resources/assets/"),
)
def test_resource_url_directories(
        resource_url_prefix: str,
        path: str,
        auth: httpx.BasicAuth,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(
        with_default_hostname(f"{resource_url_prefix}{path}"),
        auth=auth,
    )
    assert_not_found(r)


def test_short_url_main_page(
        main_page_short_url: str,
        auth: httpx.BasicAuth,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(main_page_short_url), auth=auth)
    assert_not_found(r)


def test_script_url_main_page(
        main_page_script_url: str,
        auth: httpx.BasicAuth,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(main_page_script_url), auth=auth)
    assert_not_found(r)


@pytest.mark.parametrize(
    "path",
    ("/hive/apple-touch-icon.png",
     "/resources/assets/poweredby_mediawiki_176x62.png"),
)
def test_resource_url_files(
        resource_url_prefix: str,
        path: str,
        auth: httpx.BasicAuth,
        with_default_hostname: URLRewriter,
) -> None:
    """Authenticated static resource requests serve as expected.
    """
    r = httpx.get(
        with_default_hostname(f"{resource_url_prefix}{path}"),
        auth=auth,
    )
    assert_not_found(r)
