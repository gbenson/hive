from io import BytesIO

from hive.vane_webui_api.request_handler import RequestHandler


class MockRequest:
    def __init__(self, request: bytes):
        self._vane_test_request = request
        self._vane_test_respbuf = BytesIO()

    def makefile(self, *args):
        assert args == ("rb", -1)
        request_bytes = self._vane_test_request
        assert request_bytes is not None
        self._vane_test_request = None
        return BytesIO(request_bytes)

    def sendall(self, data: bytes):
        self._vane_test_respbuf.write(data)

    @property
    def response_bytes(self) -> bytes:
        return self._vane_test_respbuf.getvalue()


class MockClientAddress:
    pass


class MockServer:
    pass


def run_test(request: bytes) -> bytes:
    request = MockRequest(request)
    client_address = ("nnn.nnn.nnn.nnn", "ppppp")
    server = MockServer()
    RequestHandler(request, client_address, server)
    return request.response_bytes


def test_login():
    response = run_test(b"GET / HTTP/1.1\r\n\r\n")
    print(response.decode())
    #assert False
