import logging
import time

from threading import Lock
from typing import IO

from hive.common.units import SECONDS

logger = logging.getLogger(__name__)


class EventStream:
    def __init__(
            self,
            wfile: IO[bytes],
            max_idle_time: float = 25 * SECONDS,
    ):
        self._wfile = wfile
        self._lock = Lock()
        self.max_idle_time = max_idle_time
        self.is_open = True
        self.last_activity = 0

    def sleep(self, secs: float):
        if time.time() + secs - self.last_activity >= self.max_idle_time:
            self.send(b"event: keepalive\ndata:\n\n")
        time.sleep(secs)

    def send(self, data: bytes):
        try:
            with self._lock:
                self._wfile.write(data)
                self.last_activity = time.time()
        except BrokenPipeError:
            self.is_open = False
        except OSError:
            logger.exception("EXCEPTION")
            self.is_open = False
