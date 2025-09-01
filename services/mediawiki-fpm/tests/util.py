import httpx

from httpx import Response


def assert_moved_permanently(r: Response, expect_location: str) -> None:
    assert r.status_code == httpx.codes.MOVED_PERMANENTLY
    assert r.has_redirect_location
    assert r.headers["location"] == expect_location
    assert "www-authenticate" not in r.headers


def assert_not_authorized(r: Response) -> None:
    assert r.status_code == httpx.codes.UNAUTHORIZED
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert r.headers["www-authenticate"] == EXPECT_WWW_AUTHENTICATE


def assert_forbidden(r: Response) -> None:
    assert r.status_code == httpx.codes.FORBIDDEN
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers


def assert_not_found(r: Response) -> None:
    assert r.status_code == httpx.codes.NOT_FOUND
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers


EXPECT_WWW_AUTHENTICATE = 'Basic realm="Authorization required"'
