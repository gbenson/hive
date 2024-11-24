from dataclasses import dataclass
from typing import Callable, Optional

from hive.common.socketserver import serving
from hive.messaging import Channel, blocking_connection

from .server import HTTPServer


@dataclass
class Service:
    server_address: tuple[str, int | str] = ("", 7224)
    on_channel_open: Optional[Callable[[Channel], None]] = None

    def run(self):
        with blocking_connection() as conn:
            channel = conn.channel()
            try:
                server = HTTPServer(self.server_address, channel=channel)
            finally:
                if self.on_channel_open:
                    # deferred so we receive our own (re)start message
                    self.on_channel_open(channel)
            with serving(server):
                channel.start_consuming()
