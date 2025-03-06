import logging
import time

from threading import Lock
from typing import IO, Optional

from hive.common.units import SECOND

logger = logging.getLogger(__name__)


class EventStream:
    def __init__(
            self,
            wfile: IO[bytes],
            max_idle_time: float = 25 * SECOND,
    ):
        self._wfile = wfile
        self._lock = Lock()
        self.max_idle_time = max_idle_time
        self.is_open = True
        self._send_queue = []

    def send(self, data: bytes, first: bool = False):
        with self._lock:
            if first:
                self._send_queue.insert(0, data)
            else:
                self._send_queue.append(data)

    def _get_bytes_to_send(self) -> Optional[bytes]:
        with self._lock:
            if (send_queue := self._send_queue):
                self._send_queue = []
            else:
                return None
        return b"".join(send_queue)

    def run(self, poll_interval=0.5):
        deadline = 0
        while self.is_open:
            data = self._get_bytes_to_send()
            if not data:
                if time.time() + poll_interval < deadline:
                    time.sleep(poll_interval)
                    continue
                data = b"event: keepalive\ndata:\n\n"
            self._send(data)
            deadline = time.time() + self.max_idle_time

    def _send(self, data: bytes):
        try:
            with self._lock:
                self._wfile.write(data)
        except BrokenPipeError:
            self.is_open = False
        except OSError:
            logger.exception("EXCEPTION")
            self.is_open = False
