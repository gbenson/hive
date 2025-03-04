from enum import Enum, auto


class Semantics(Enum):
    PUBLISH_SUBSCRIBE = auto()    # events
    COMPETING_CONSUMERS = auto()  # requests
