from dataclasses import dataclass

from hive.common.socketserver import serving
from hive.service import HiveService

from .server import HTTPServer


@dataclass
class Service(HiveService):
    server_address: tuple[str, int | str] = ("", 7224)

    def run(self):
        with self.blocking_connection(on_channel_open=None) as conn:
            channel = conn.channel()
            try:
                server = HTTPServer(self.server_address, channel=channel)
            finally:
                if self.on_channel_open:
                    # deferred so we receive our own restart monitor message
                    self.on_channel_open(channel)
            with serving(server):
                channel.start_consuming()
