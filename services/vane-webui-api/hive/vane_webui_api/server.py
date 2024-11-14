import json
import logging

from contextlib import contextmanager
from datetime import datetime, timezone
from functools import cached_property, partial
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from secrets import token_urlsafe
from threading import Lock
from typing import Any, IO, Optional
from uuid import RFC_4122, UUID, uuid4

from pika import BasicProperties
from pika.spec import Basic

from valkey import Valkey

from hive.common.units import DAYS, MINUTE
from hive.messaging import Channel

from .authenticator import Authenticator
from .event_stream import EventStream
from .exceptions import HTTPError
from .request_handler import RequestHandler

logger = logging.getLogger(__name__)


class HTTPServer(ThreadingHTTPServer):
    def __init__(
            self,
            server_address: tuple[str, int | str] = ("", 80),
            handler_class: type[RequestHandler] = RequestHandler,
            *,
            channel: Channel,
            queue_name: str = "chat.messages",
            key_value_store_url: str = "valkey://vane-valkey",
            csrf_token_lifetime: float = 1 * MINUTE,
            session_id_lifetime: float = 28 * DAYS,
            message_lifetime: float = 60 * DAYS,
            num_initial_events_to_send: int = 20,
            authenticator: Optional[Authenticator] = None,
            **kwargs,
    ):
        super().__init__(server_address, handler_class, **kwargs)
        self._streams_lock = Lock()
        self._streams = []
        self._channel = channel
        self._queue_name = queue_name
        self._valkey_url = key_value_store_url
        self._csrf_token_lifetime = csrf_token_lifetime
        self._session_id_lifetime = session_id_lifetime
        self._message_lifetime = message_lifetime
        self._num_initial_events_to_send = num_initial_events_to_send

        if authenticator is None:
            authenticator = Authenticator()
        self._auth = authenticator

        self._channel.consume_events(
            queue=queue_name,
            on_message_callback=self.forward_message_to_clients,
        )

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self._valkey_url)

    def get_login_token(self, client_address: tuple) -> str:
        client_id = ":".join(list(map(str, client_address)))
        bound_key = f"client:{client_id}:login_token"
        for is_retry in (False, True):
            if (token := self._valkey.get(bound_key)):
                return token.decode("utf-8")
            token = token_urlsafe()
            lifetime_ms = int(self._csrf_token_lifetime * 1000)
            if self._valkey.set(bound_key, token, nx=True, px=lifetime_ms):
                break

            # bound_key didn't exist for our GET, but it does now.
            # This could happen if the client sent multiple login
            # checks in parallel, in which case we should now get
            # a token if we retry the GET.
            if not is_retry:
                continue

            # We only retry once, since it shouldn't be possible for
            # the second GET to fail unless we somehow serviced two
            # near-simultaneous get_login_token calls while at the
            # same time being so overloaded that the token expired
            # before the second GET returned.  If this does happen
            # then something is seriously wrong.
            raise HTTPError(HTTPStatus.TOO_MANY_REQUESTS)

        token_key = f"login_token:{token}"
        self._valkey.set(token_key, client_id, nx=True, px=lifetime_ms)
        return token

    def authenticate(self, creds: dict[str, str], request: RequestHandler):
        login_token = creds.get("csrf")
        if not login_token:
            return None
        token_key = f"login_token:{login_token}"
        if not self._valkey.delete(token_key):
            return None
        username = creds.get("user")
        if not self._auth.authenticate(username, creds.get("pass")):
            return None
        session_id = token_urlsafe()
        login_key = f"session:{session_id}"
        lifetime = round(self._session_id_lifetime)
        login_info = json.dumps({
            "username": username,
            "headers": request.headers.items(),
        }, separators=(",", ":"))
        if not self._valkey.set(login_key, login_info, nx=True, ex=lifetime):
            raise ValueError(login_key)
        return session_id

    def is_logged_in(self, session_id: str) -> bool:
        return bool(self._valkey.get(f"session:{session_id}"))

    def publish_message_from_client(self, message: dict[str, Any]):
        self._channel.connection.add_callback_threadsafe(partial(
            self._channel.publish_event,
            message=self._sanitize_message(message),
            routing_key=self._queue_name,
        ))

    @staticmethod
    def _sanitize_message(message: dict[str, Any]) -> dict[str, Any]:
        sender = message.get("sender", "user")
        if sender != "user":
            logger.error("%r: bad sender", message)
            raise HTTPError(HTTPStatus.BAD_REQUEST)
        text = message.get("text")
        if not text:
            logger.error('%r: no "text"', message)
            raise HTTPError(HTTPStatus.BAD_REQUEST)
        uuid = message.get("uuid")
        if not uuid:
            uuid = uuid4()
        else:
            try:
                uuid = UUID(message.get("uuid", ""))
                if uuid.variant != RFC_4122:
                    raise ValueError(uuid.variant)
                if uuid.version != 4:
                    raise ValueError(uuid.version)
            except ValueError:
                logger.exception("EXCEPTION")
                raise HTTPError(HTTPStatus.BAD_REQUEST)
        uuid = str(uuid)
        return {
            "sender": sender,
            "text": text,
            "uuid": uuid,
            "timestamp": str(datetime.now(tz=timezone.utc)),
        }

    def forward_message_to_clients(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        message = json.loads(body)

        timestamp = message["timestamp"]
        timestamp = datetime.fromisoformat(timestamp)
        timestamp = timestamp.timestamp()

        message_id = message["uuid"]
        message_key = f"message:{message_id}"
        expire_at = round(timestamp + self._message_lifetime)

        self._valkey.set(message_key, body, exat=expire_at)
        self._valkey.zadd("messages", {message_id: timestamp})

        self.send_event(b"[" + body + b"]")

    @contextmanager
    def new_event_stream(self, wfile: IO[bytes]):
        stream = EventStream(wfile)
        with self._streams_lock:
            self._streams.append(stream)
            self._send_initial_events(stream)
        try:
            yield stream
        finally:
            with self._streams_lock:
                self._streams.remove(stream)

    def _send_initial_events(self, stream: EventStream):
        message_ids = [
            message_id.decode("utf-8")
            for message_id in reversed(
                    self._valkey.zrange(
                        "messages",
                        0,
                        self._num_initial_events_to_send - 1,
                        desc=True,
                    ))
        ]
        if not message_ids:
            return
        message_keys = [
            f"message:{message_id}"
            for message_id in message_ids
        ]
        event = b",".join(
            body
            for body in self._valkey.mget(*message_keys)
            if body
        )
        if b"\n\n" in event:
            raise ValueError(event)
        event = b"".join((b"data: [", event, b"]\n\n"))
        stream.send(event)

    def send_event(self, data: str | bytes, name: Optional[str] = None):
        if isinstance(data, str):
            data = data.encode("utf-8")
        event = bytearray()
        if name:
            event += f"event: {name}\n".encode("utf-8")
        event += b"data: "
        event += data
        if b"\n\n" in event:
            raise ValueError(event)
        event += b"\n\n"
        with self._streams_lock:
            for stream in self._streams:
                stream.send(event)