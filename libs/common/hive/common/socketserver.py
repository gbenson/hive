import logging

from contextlib import contextmanager
from socketserver import BaseServer
from threading import Thread

from .units import SECONDS

logger = logging.getLogger(__name__)


@contextmanager
def serving(
        server: BaseServer,
        *,
        shutdown_timeout: float = 30 * SECONDS,
        daemon: bool = True,
) -> Thread:
    """Run a :class:`socketserver.BaseServer` in another thread.
    """
    thread = Thread(target=server.serve_forever, daemon=daemon)
    logger.info("%s:%s: Starting server", thread, server)
    thread.start()
    try:
        logger.info("%s:%s: Server started", thread, server)
        yield thread
    finally:
        logger.info("%s: %s: Stopping server", thread, server)
        server.shutdown()
        logger.debug("%s: Waiting for thread exit", thread)
        thread.join(timeout=30 * SECONDS)
        logger.info("%s: %s: Server stopped", thread, server)
