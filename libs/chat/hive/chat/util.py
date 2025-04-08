from dataclasses import dataclass

from hive.messaging import Channel, blocking_connection


@dataclass
class channelfunc:
    name: str

    def __call__(self, *args, **kwargs):
        if (channel := kwargs.pop("channel", None)):
            return self._call(channel, *args, **kwargs)
        with blocking_connection(connection_attempts=1) as conn:
            return self._call(conn.channel(), *args, **kwargs)

    def _call(self, channel: Channel, *args, **kwargs):
        return getattr(channel, self.name)(*args, **kwargs)


publish_event = channelfunc("publish_event")
