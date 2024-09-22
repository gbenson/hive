from __future__ import annotations

import email
import email.policy
import logging

from contextlib import closing
from functools import cached_property
from imaplib import IMAP4_SSL, IMAP4_SSL_PORT

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
    def _unmarshalled(self):
        return email.message_from_bytes(
            self._marshalled,
            policy=email.policy.default,
        )

    def __getitem__(self, key: str):
        return self._unmarshalled[key]

    def __bytes__(self) -> bytes:
        return self._marshalled

    def delete(self):
        must(self._conn.uid("STORE", self._uid, "+FLAGS", r"\Deleted"))
