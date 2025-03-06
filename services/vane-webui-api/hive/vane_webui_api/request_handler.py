import json
import logging

from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from typing import Optional

from valkey.exceptions import ConnectionError

from hive.common.units import DAY

from .exceptions import HTTPError
from .route import Route

logger = logging.getLogger(__name__)


class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _handle_request(self):
        try:
            self.route_api_request()
        except HTTPError as e:
            self.send_error(e.status)
        except ConnectionError:
            logger.exception("EXCEPTION")
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("EXCEPTION")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    do_GET = _handle_request
    do_HEAD = _handle_request
    do_POST = _handle_request

    def route_api_request(self):
        route = Route.from_path(self.path)
        if not route:
            raise HTTPError(HTTPStatus.NOT_FOUND)
        method = self._handler_for(route)
        if not method:
            raise HTTPError(HTTPStatus.METHOD_NOT_ALLOWED)
        if route is not Route.LOGIN and not self.is_logged_in:
            raise HTTPError(HTTPStatus.UNAUTHORIZED)
        method()

    def _handler_for(self, route: Route):
        route_name = route.name.lower()
        http_method = self.command.lower()
        if http_method == "head":
            http_method = "get"
        mname = f"_do_{http_method}_{route_name}"
        return getattr(self, mname, None)

    SESSION_ID_COOKIE = "sessionId"

    @property
    def is_logged_in(self) -> bool:
        session_id = self.get_cookie(self.SESSION_ID_COOKIE)
        if not session_id:
            return False
        return self.server.is_logged_in(session_id)

    def _do_get_login(self):
        if not self.is_logged_in:
            self.send_csrf_token()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _do_post_login(self):
        creds = self.read_json_payload()
        session_id = self.server.authenticate(creds, self)
        if not session_id:
            self.send_csrf_token()
            return

        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_set_cookie(
            self.SESSION_ID_COOKIE,
            session_id,
            max_age=(365 * DAY) // 12,
            secure=True,
            samesite="strict",
            httponly=True,
        )
        self.end_headers()

    def _do_get_events(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command == "HEAD":
            return

        with self.server.new_event_stream(self.wfile) as stream:
            stream.run()

    def _do_post_chat(self):
        message = self.read_json_payload()
        self.server.publish_message_from_client(message)
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def read_json_payload(self, max_length=1024):
        if self.command != "POST":
            raise ValueError(self.command)
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            raise HTTPError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        content_length_str = self.headers.get("content-length", None)
        if not content_length_str:
            raise HTTPError(HTTPStatus.LENGTH_REQUIRED)
        try:
            content_length = int(content_length_str)
            if content_length == 0:
                raise HTTPError(HTTPStatus.LENGTH_REQUIRED)
            if content_length < 0:
                raise ValueError(content_length_str)
            if str(content_length) != content_length_str:
                raise ValueError(content_length_str)
        except ValueError:
            logger.exception("EXCEPTION")
            raise HTTPError(HTTPStatus.BAD_REQUEST)
        if max_length > 0 and content_length > max_length:
            raise HTTPError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        payload = self.rfile.read(content_length)
        if len(payload) != content_length:
            logger.error(
                "content_length mismatch: %s != %s",
                len(payload),
                content_length,
            )
            raise HTTPError(HTTPStatus.BAD_REQUEST)
        try:
            return json.loads(payload)
        except Exception:
            logger.exception("EXCEPTION")
            raise HTTPError(HTTPStatus.BAD_REQUEST)

    def get_cookie(self, name, failobj=None) -> Optional[str]:
        for header in self.headers.get_all("cookie", ()):
            for cookie in header.split(";"):
                try:
                    got_name, value = cookie.strip().split("=", 1)
                except ValueError:
                    logger.exception("EXCEPTION")
                    raise HTTPError(HTTPStatus.BAD_REQUEST)
                if got_name == name:
                    return value
        return failobj

    def send_set_cookie(self, name, value, **kwargs):
        cookie = SimpleCookie()
        cookie[name] = value
        for attr, value in kwargs.items():
            cookie[name][attr.replace("_", "-")] = value
        self.send_header(*cookie.output().split(": ", 1))

    def send_csrf_token(self):
        self.send_json({
            "csrf": self.server.get_login_token(self.client_address),
        })

    def send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        if self.command == "HEAD":
            return
        self.wfile.write(body)
