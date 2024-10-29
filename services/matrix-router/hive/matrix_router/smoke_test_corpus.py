import os

from functools import cached_property
from hashlib import sha256


class Corpus:
    DIRNAME_VAR = "HIVE_MATRIX_EVENT_CORPUS"

    @cached_property
    def _dirname(self):
        dirname = os.environ.get(self.DIRNAME_VAR)
        if not dirname:
            return None
        gitignore = os.path.join(dirname, ".gitignore")
        if not os.path.exists(gitignore):
            return None
        return dirname

    def maybe_add_event(self, event: bytes):
        dirname = self._dirname
        if not dirname:
            return
        basename = sha256(event).hexdigest()
        filename = os.path.join(dirname, basename + ".json")
        with open(filename, "wb") as fp:
            fp.write(event)


DEFAULT_CORPUS = Corpus()

maybe_add_event = DEFAULT_CORPUS.maybe_add_event
