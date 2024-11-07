from http import HTTPStatus

import pytest
import requests


@pytest.mark.parametrize("method", ("PUT", "CLINK"))
@pytest.mark.parametrize("route", ("login", "events", "chat", "clank"))
def test_not_implemented(mock_server, method, route):
    """Unimplemented methods result in 501 Not Implemented.
    """
    url = f"{mock_server.url}/{route}"
    r = requests.request(method, url)
    assert r.status_code == HTTPStatus.NOT_IMPLEMENTED
