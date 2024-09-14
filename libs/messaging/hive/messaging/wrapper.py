class WrappedPikaThing:
    def __init__(self, pika):
        self._pika = pika

    def __getattr__(self, attr):
        return getattr(self._pika, attr)
