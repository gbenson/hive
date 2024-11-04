import json
import os
import subprocess

from http import HTTPStatus
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from secrets import token_urlsafe


class TestHTTPRequestHandler(SimpleHTTPRequestHandler):
    SESSION_ID = f"sessionId={token_urlsafe()}"
    CSRF_TOKEN = token_urlsafe()
    LOGIN_PATH = "/api/login"

    def do_GET(self):
        match self.path:
            case self.LOGIN_PATH:
                self._do_login()
            case _:
                super().do_GET()

    def do_POST(self):
        match self.path:
            case self.LOGIN_PATH:
                self._do_login()
            case _:
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Not implemented",
                )

    def _do_login(self):
        assert self.path == self.LOGIN_PATH
        for cookie in self.headers.get("cookie", "").split(";"):
            cookie = cookie.strip()
            if cookie == self.SESSION_ID:
                self._send_got_session()
                return
            if cookie.split("=", 1)[0] == "sessionId":
                break
        if self.command == "POST":
            content_type = self.headers.get_content_type()
            assert content_type == "application/json"
            content_length = int(self.headers.get("content-length", "0"))
            assert content_length
            body = json.loads(self.rfile.read(content_length))
            if body == {"user": "gary",
                        "pass": "password",
                        "csrf": self.CSRF_TOKEN}:
                self._send_set_session()
                return
        self.send_json({"csrf": self.CSRF_TOKEN})

    def _send_got_session(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()
        self.wfile.flush()

    def _send_set_session(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header(
            "Set-Cookie", "; ".join((
                self.SESSION_ID,
                f"Max-Age={1<<25}",
                "SameSite=Strict",
                "HttpOnly",
                "Secure",
            )))
        self.end_headers()
        self.wfile.flush()

    def send_json(self, body):
        body = json.dumps(body).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()


def main(server_address=("127.0.0.1", 5678)):
    httpd = ThreadingHTTPServer(server_address, TestHTTPRequestHandler)
    host, port = httpd.server_address
    server_url = f"http://{host}:{port}/"
    print(f"Serving HTTP on: {server_url}")
    try:
        subprocess.check_call(("xdg-open", server_url))
    except Exception as e:
        print(f"Failed to open browser: {e}")
    os.chdir(os.path.join(os.path.dirname(__file__), "vane_webui"))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
