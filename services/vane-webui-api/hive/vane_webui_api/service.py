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
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            server = HTTPServer(self.server_address, channel=channel)
            with serving(server):
                channel.start_consuming()
