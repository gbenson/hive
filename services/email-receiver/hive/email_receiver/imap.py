from __future__ import annotations

import logging

from contextlib import closing
from functools import cached_property
from imaplib import IMAP4_SSL, IMAP4_SSL_PORT

from hive.email import EmailMessage

logger = logging.getLogger(__name__)
d = logger.debug


class Client:
    def __init__(self, config: dict):
        self.host = config["host"]
        self.port = int(config.get("port", IMAP4_SSL_PORT))
        auth_config = config["auth"]
        self.user = auth_config["username"]
        self.password = auth_config["password"]

    def connect(self) -> ClientConnection:
        return ClientConnection(self)


def must(typ_dat):
    d("%s", typ_dat)
    typ, dat = typ_dat
    if typ != "OK":
        raise ClientConnection.error(dat[-1].decode(errors="ignore"))
    return dat


class ClientConnection(IMAP4_SSL):
    def __init__(self, client: Client):
        logger.info("Connecting to %s:%d", client.host, client.port)
        try:
            super().__init__(host=client.host, port=client.port)
            d("Authenticating")
            must(self.login(client.user, client.password))

        except Exception:
            try:
                self.shutdown()
            except Exception:
                pass
            raise

    def logout(self):
        logger.info("Logging out")
        return super().logout()

    def shutdown(self):
        logger.info("Closing connection to %s:%s", self.host, self.port)
        return super().shutdown()

    def select(self, mailbox: str) -> Mailbox:
        d("Selecting %s", mailbox)
        data = must(super().select(mailbox))
        return closing(Mailbox(self, mailbox, data))


class Mailbox:
    def __init__(self, conn: ClientConnection, name: str, select_response):
        self.name = name
        self._conn = conn
        self._num_messages = None
        try:
            self._num_messages = int(select_response[0])
        except Exception:
            logger.error("EXCEPTION%r:", select_response, exc_info=True)
        d("%s selected: %s messages", self.name, self._num_messages)

    def close(self):
        d("Closing %r", self.name)
        must(self._conn.close())

    @property
    def messages_by_id(self):
        if not self._num_messages:
            return

        for data in must(self._conn.fetch(
                "1:*",
                "(UID BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])",
        )):
            # Each data is either bytes or a tuple.
            if not isinstance(data, tuple):
                if data != b")":  # XXX why?
                    logger.warning("data: %r", data)
                continue

            # If a tuple, then the first part is the header
            # of the response, and the second part contains
            # the data (ie: 'literal' value).
            header, data = data
            header = header.split()
            if header[1] != b"(UID" or (
                    header[-2] != b"(MESSAGE-ID)]" or
                    header[-1] != b"{%d}" % len(data)):
                logger.warning("header: %r", header)
                continue
            uid = header[2]

            name_value = data.split(b":", 1)
            if len(name_value) != 2:
                if data == b"\r\n":
                    continue  # A message with no Message-ID
                logger.warning("data: %r", data)
                continue
            name, value = name_value
            if name.strip().lower() != b"message-id":
                logger.warning("data: %r", data)
                continue
            message_id = value.strip()
            if not message_id:
                logger.warning("data: %r", data)
                continue

            yield MessageByID(self._conn, uid, message_id)

    @property
    def messages(self):
        if not self._num_messages:
            return

        for data in must(self._conn.fetch("1:*", "(UID RFC822)")):
            # Each data is either bytes or a tuple.
            if not isinstance(data, tuple):
                if data != b")":  # XXX why?
                    logger.warning("data: %r", data)
                continue

            # If a tuple, then the first part is the header
            # of the response, and the second part contains
            # the data (ie: 'literal' value).
            header, data = data
            header = header.split()
            if header[1] != b"(UID" or (
                    header[-2] != b"RFC822" or
                    header[-1] != b"{%d}" % len(data)):
                logger.warning("header: %r", header)
                continue
            uid = header[2]
            yield Message(self._conn, uid, data)


class MessageByID:
    def __init__(
            self,
            conn: ClientConnection,
            uid: int,
            message_id: bytes,
    ):
        self._conn = conn
        self._uid = uid
        self.message_id = message_id

    def _get_message_bytes(self):
        for data in must(self._conn.uid(
                "FETCH",
                self._uid,
                "(UID BODY.PEEK[])",
        )):
            # Each data is either bytes or a tuple.
            if not isinstance(data, tuple):
                if data != b")":  # XXX why?
                    logger.warning("data: %r", data)
                continue

            # If a tuple, then the first part is the header
            # of the response, and the second part contains
            # the data (ie: 'literal' value).
            header, message_bytes = data
            header = header.split()
            if header[1] != b"(UID" or (
                    header[2] != self._uid or
                    header[-2] != b"BODY[]" or
                    header[-1] != b"{%d}" % len(message_bytes)):
                logger.warning("header: %r", header)
                continue

            yield message_bytes

    def get_message_bytes(self):
        all_results = list(self._get_message_bytes())
        checked_results = list(filter(
            self._message_bytes_has_message_id,
            all_results,
        ))
        num_variants = len(checked_results)
        if num_variants == 1:
            return checked_results[0]  # yay!

        message_id = self.message_id.decode()
        if num_variants > 1:
            logger.warning(f"got {num_variants} versions of {message_id}")
            return None

        assert not num_variants
        if not all_results:
            logger.warning(f"got nothing for {message_id}")
            return None

        num_variants = len(all_results)
        logger.warning(f"got {num_variants} non-matches for {message_id}")
        return None

    def _message_bytes_has_message_id(self, data):
        return self._message_id_from_message_bytes(data) == self.message_id

    @staticmethod
    def _message_id_from_message_bytes(data):
        in_continuation = False
        for line in data.split(b"\n"):
            if not (line := line.rstrip()):
                break  # end of headers
            if in_continuation:
                value = line.lstrip()
                if value == line:
                    break  # not a continuation?
                return value.rstrip()
            if not line.lower().startswith(b"message-id"):
                continue
            check, value = line.split(b":", 1)
            if check.rstrip().lower() != b"message-id":
                continue
            if value:
                return value.strip()
            in_continuation = True
        return None


class Message:
    def __init__(
            self,
            conn: ClientConnection,
            uid: int,
            data: bytes,
    ):
        self._conn = conn
        self._uid = uid
        self._marshalled = data

    @property
    def server(self) -> str:
        return self._conn.host

    @property
    def uid(self) -> str:
        return str(int(self._uid))

    @cached_property
    def _unmarshalled(self) -> EmailMessage:
        return EmailMessage.from_bytes(self._marshalled)

    def __getitem__(self, key: str):
        return getattr(self._unmarshalled, key.lower())

    @cached_property
    def summary(self):
        return self._unmarshalled.summary

    def delete(self):
        must(self._conn.uid("STORE", self._uid, "+FLAGS", r"\Deleted"))
