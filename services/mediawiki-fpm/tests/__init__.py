import httpx

from httpx import Response


def assert_moved_permanently(r: Response, expect_location: str) -> None:
    assert r.status_code == httpx.codes.MOVED_PERMANENTLY
    assert r.has_redirect_location
    assert r.headers["location"] == expect_location
    assert "www-authenticate" not in r.headers
    assert r.text == EXPECT_301_RESPONSE_BODY


def assert_not_authorized(r: Response) -> None:
    assert r.status_code == httpx.codes.UNAUTHORIZED
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert r.headers["www-authenticate"] == EXPECT_WWW_AUTHENTICATE
    assert r.text == EXPECT_401_RESPONSE_BODY


def assert_not_found(r: Response) -> None:
    assert r.status_code == httpx.codes.NOT_FOUND
    assert not r.has_redirect_location
    assert "location" not in r.headers
    assert "www-authenticate" not in r.headers
    assert r.text == EXPECT_404_RESPONSE_BODY


EXPECT_301_RESPONSE_BODY = """\
<html>
<head><title>301 Moved Permanently</title></head>
<body>
<center><h1>301 Moved Permanently</h1></center>
<hr><center>nginx</center>
</body>
</html>
""".replace("\n", "\r\n")


EXPECT_401_RESPONSE_BODY = """\
<html>
<head><title>401 Authorization Required</title></head>
<body>
<center><h1>401 Authorization Required</h1></center>
<hr><center>nginx</center>
</body>
</html>
""".replace("\n", "\r\n")


EXPECT_404_RESPONSE_BODY = """\
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>
""".replace("\n", "\r\n")


EXPECT_WWW_AUTHENTICATE = 'Basic realm="Authorization required"'
