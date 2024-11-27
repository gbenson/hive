class SmallCircularBuffer:
    def __init__(self, num_items, coerce=None):
        sentinel = object()
        if not coerce:
            coerce = lambda x: x  # noqa: E731
        self._coerce = coerce
        self._items = [sentinel] * num_items
        self._index = 0

    def __contains__(self, item):
        return self._coerce(item) in self._items

    def add(self, item):
        self._items[self._index] = self._coerce(item)
        self._index = (self._index + 1) % len(self._items)
