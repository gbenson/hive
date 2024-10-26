import logging

from hive.messaging import Channel

from .event import MatrixEvent

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


class Router:
    def on_matrix_event(
            self,
            channel: Channel,
            event: MatrixEvent,
    ):
        raise NotImplementedError(event.json())
