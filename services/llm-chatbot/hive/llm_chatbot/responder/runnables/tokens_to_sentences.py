import re

from collections.abc import Iterator

SEP = re.compile(r"((?:(?:(?<=\D)\.(?=\D))|\n)\s*)", re.DOTALL)


def tokens_to_sentences(input: Iterator[str]) -> Iterator[str]:
    buf = ""
    for token in input:
        buf += token
        splits = SEP.split(buf, maxsplit=1)
        if len(splits) == 1:
            continue
        assert len(splits) == 3
        before, sep, after = splits
        if not any(c.isalpha() for c in after):
            continue
        yield before + sep
        buf = after
    if (sentence := buf):
        yield sentence
