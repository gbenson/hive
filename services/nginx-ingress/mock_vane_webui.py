import json
import os
import subprocess
import time

from contextlib import contextmanager
from http import HTTPStatus
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from secrets import token_urlsafe
from threading import Lock
from typing import Optional


class HTTPRequestHandler(SimpleHTTPRequestHandler):
    SESSION_ID = f"sessionId={token_urlsafe()}"
    CSRF_TOKEN = token_urlsafe()
    LOGIN_PATH = "/api/login"
    EVENTS_PATH = "/api/events"
    CHAT_PATH = "/api/chat"

    def do_GET(self):
        match self.path:
            case self.LOGIN_PATH:
                self._do_login()
            case self.EVENTS_PATH:
                self._do_events()
            case _:
                super().do_GET()

    def do_POST(self):
        match self.path:
            case self.LOGIN_PATH:
                self._do_login()
            case self.CHAT_PATH:
                self._do_chat()
            case _:
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Not implemented",
                )

    def _do_login(self):
        for cookie in self.headers.get("cookie", "").split(";"):
            cookie = cookie.strip()
            if cookie == self.SESSION_ID:
                self.send_no_content()
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

    def send_no_content(self):
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

    def _do_events(self, poll_interval=0.5):
        self.send_response(HTTPStatus.OK)
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        with self.server.new_event_stream(self.wfile) as stream:
            while stream.is_open:
                time.sleep(poll_interval)

    def _do_chat(self):
        content_type = self.headers.get_content_type()
        assert content_type == "application/json"
        content_length = int(self.headers.get("content-length", "0"))
        assert content_length
        body = json.loads(self.rfile.read(content_length))
        assert body.get("sender") == "user"
        time.sleep(0.5)
        self.send_no_content()
        time.sleep(1)
        self.server.send_messages(
            {"sender": "hive", "text": "vvv"},
            body,
            {"sender": "hive", "text": "^^^"},
        )


class HTTPServer(ThreadingHTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._streams_lock = Lock()
        self._streams = []

    @contextmanager
    def new_event_stream(self, wfile):
        stream = EventStream(wfile)
        with self._streams_lock:
            self._streams.append(stream)
            self._send_initial_events(stream)
        try:
            yield stream
        finally:
            with self._streams_lock:
                self._streams.remove(stream)

    def _send_initial_events(self, stream):
        event = json.dumps([
            {"sender": "hive", "text": "Hello this is HIVE CHAT"},
            {"sender": "user", "text": "wow, that's interesting!"},
            {"sender": "hive", "text": "sure is bucko"},
        ])
        if "\n\n" in event:
            raise ValueError(event)
        stream.send(f"data: {event}\n\n".encode("utf-8"))

    def send_messages(self, *messages):
        self.send_event("", json.dumps(messages))

    def send_event(self, event_type: str, event: str):
        event = f"data: {event}"
        if event_type:
            event = f"event: {event_type}\n{event}"
        if "\n\n" in event:
            raise ValueError(event)
        event = f"{event}\n\n".encode("utf-8")
        with self._streams_lock:
            for stream in self._streams:
                stream.send(event)


class EventStream:
    def __init__(self, wfile):
        self._wfile = wfile
        self.is_open = True

    def send(self, data: bytes):
        try:
            self._wfile.write(data)
            self._wfile.flush()

        except BrokenPipeError:
            self.is_open = False


def main(server_address=("127.0.0.1", 5678)):
    httpd = HTTPServer(server_address, HTTPRequestHandler)
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
