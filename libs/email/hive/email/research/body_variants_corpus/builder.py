import json
import logging
import os

from functools import cached_property
from typing import Optional

from ... import load_email
from ...optional.openai import OpenAI
from ...testing import RESOURCEDIR, serialized_email_filenames
from .example import Example

logger = logging.getLogger(__name__)
d = logger.debug
info = logger.info


class CorpusBuilder:
    def main(self):
        logging.basicConfig(level=logging.DEBUG)
        for filename in serialized_email_filenames():
            self.maybe_add_example(filename)

    def __init__(self, filename: Optional[str] = None):
        if filename is None:
            filename = os.path.join(
                RESOURCEDIR,
                "body-variants-corpus.jsonl",
            )
        self._filename = filename

    @cached_property
    def examples(self):
        try:
            return dict(
                (example._id, example)
                for example in self.read_examples()
            )
        except FileNotFoundError:
            return {}

    def read_examples(self, filename: Optional[str] = None):
        with open(filename or self._filename) as fp:
            return map(Example.from_json, fp.readlines())

    def add_example(self, example: Example):
        assert example._id not in self.examples
        serialized = json.dumps(example.as_dict())
        with open(self._filename, "a") as fp:
            fp.write(serialized)
            fp.write("\n")

    @cached_property
    def openai(self):
        return OpenAI()

    def maybe_add_example(self, filename: str):
        example_id = os.path.relpath(filename, RESOURCEDIR)
        if example_id in self.examples:
            d("%s: already in corpus", example_id)
            return

        msg = load_email(filename)

        plaintext_variant = msg.plain_content
        if not plaintext_variant:
            d("%s: no text variant", example_id)
            return

        from_html_variant = msg.plain_content_from_html_content
        if not from_html_variant:
            d("%s: no HTML variant", example_id)
            return

        if from_html_variant == plaintext_variant:
            d("%s: variants have identical content", example_id)
            return

        logger.info("%s", os.path.relpath(filename))
        d("PREFERRED:\n%s", plaintext_variant)
        d("ALTERNATE:\n%s", from_html_variant)

        example = Example(example_id, plaintext_variant, from_html_variant)
        example.categorize(self.openai)
        d("RESULT: %s", example.best_variant)
        self.add_example(example)
