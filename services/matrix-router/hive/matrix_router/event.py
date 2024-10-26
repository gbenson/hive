from typing import Any


class MatrixEvent:
    def __init__(self, serialized_event: dict[str, Any]):
        self._event = serialized_event

    def json(self) -> dict[str, Any]:
        return self._event
