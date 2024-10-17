import json
import logging
import os

from collections import defaultdict
from enum import Enum, auto
from functools import cached_property
from typing import Optional

from ... import load_email
from ...analysis import bag_of_words
from ...optional.openai import OpenAI
from ...testing import RESOURCEDIR, serialized_email_filenames
from .example import Example

logger = logging.getLogger(__name__)
d = logger.debug
info = logger.info


class Status(Enum):
    ALREADY_IN_CORPUS = auto()
    NO_PLAIN_VERSION = auto()
    NO_HTML_VERSION = auto()
    IDENTICAL_CONTENT = auto()
    IDENTICAL_WORDS = auto()
    CATEGORY_COMPLETE = auto()
    CATEGORY_PLACEHOLDER = auto()
    ANALYSIS_FAILED = auto()
    HALLUCINATION = auto()


class CorpusBuilder:
    def main(self):
        logging.basicConfig(level=logging.DEBUG)
        status_counts = defaultdict(int)
        for filename in serialized_email_filenames():
            status = self.maybe_add_example(filename)
            status_counts[status] += 1
        for status, count in status_counts.items():
            print(f"{count:6d}  {status.name}")

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

    def maybe_add_example(self, filename: str) -> Status:
        example_id = os.path.relpath(filename, RESOURCEDIR)
        if example_id in self.examples:
            d("%s: already in corpus", example_id)
            return Status.ALREADY_IN_CORPUS

        msg = load_email(filename)

        plaintext_variant = msg.plain_content
        if not plaintext_variant:
            d("%s: no text variant", example_id)
            return Status.NO_PLAIN_VERSION

        from_html_variant = msg.plain_content_from_html_content
        if not from_html_variant:
            d("%s: no HTML variant", example_id)
            return Status.NO_HTML_VERSION

        if from_html_variant == plaintext_variant:
            d("%s: variants have identical content", example_id)
            return Status.IDENTICAL_CONTENT

        plaintext_words = bag_of_words(plaintext_variant)
        from_html_words = bag_of_words(from_html_variant)
        if from_html_words == plaintext_words:
            assert plaintext_words
            d("%s: variants have identical words", example_id)
            return Status.IDENTICAL_WORDS

        logger.info("%s", os.path.relpath(filename))
        d("PLAINTEXT:\n%s", plaintext_variant)
        d("FROM HTML:\n%s", from_html_variant)

        example = Example(example_id, plaintext_variant, msg.html_content)
        example.categorize(self.openai)

        match example.category:
            case "complete":
                status = Status.CATEGORY_COMPLETE
            case "placeholder":
                status = Status.CATEGORY_PLACEHOLDER
            case None:
                return Status.ANALYSIS_FAILED
            case _:
                return Status.HALLUCINATION

        self.add_example(example)
        return status
