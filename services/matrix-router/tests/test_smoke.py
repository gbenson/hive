import json
import os

import pytest

from hive.matrix_router.event import MatrixEvent
from hive.matrix_router.router import Router


def serialized_event_filenames():
    testdir = os.path.dirname(__file__)
    for dirpath, dirnames, filenames in os.walk(testdir):
        for filepath in sorted(
                os.path.join(dirpath, filename)
                for filename in filenames
                if filename.endswith(".json")):
            yield filepath


@pytest.mark.parametrize("filename", serialized_event_filenames())
def test_smoke(filename):
    router = Router()
    with open(filename) as fp:
        event = MatrixEvent(json.load(fp))
    router.on_matrix_event(MockChannel(), event)


class MockChannel:
    pass
