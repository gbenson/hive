import logging
import socket

from contextlib import closing
from errno import ECONNREFUSED

import pytest

from hive.messaging import MessageBus

logger = logging.getLogger(__name__)


def test_broker_not_listening(test_credentials):
    """Test what happens when the broker hostname resolves
    but there's nothing listening on the port.
    """
    with closing(socket.socket()) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", 0))
        host, port = s.getsockname()
    logger.info("NOT listening on %s", (host, port))
    msgbus = MessageBus(host=host, port=port)

    with pytest.raises(ConnectionRefusedError) as excinfo:
        msgbus.blocking_connection(connection_attempts=1)
    e = excinfo.value
    assert e.errno == ECONNREFUSED
    assert e.strerror == "Connection refused"


def test_broker_not_responding(test_credentials):
    """Test what happens when the broker is listening but doesn't
    respond in any reasonable time.  Most times this would end up
    being a "no route to host", but Pika doesn't expose enough to
    decide if that's happening.
    """
    with closing(socket.socket()) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", 0))
        host, port = s.getsockname()

        logger.info("kinda listening on %s", (host, port))
        msgbus = MessageBus(host=host, port=port)

        with pytest.raises(TimeoutError):
            msgbus.blocking_connection(
                connection_attempts=1,
                socket_timeout=1e-12,  # Impossibly fast...
            )
