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
        msgbus.blocking_connection()
    e = excinfo.value
    assert e.errno == ECONNREFUSED
    assert e.strerror == "Connection refused"
