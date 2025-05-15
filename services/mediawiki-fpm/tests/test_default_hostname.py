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


def test_short_url_root(
        short_url_prefix: str,
        auth: httpx.BasicAuth,
        with_default_hostname: URLRewriter,
) -> None:
    r = httpx.get(with_default_hostname(f"{short_url_prefix}/"), auth=auth)
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
