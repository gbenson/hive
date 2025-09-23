import re

from collections.abc import Iterator

SEP = re.compile(r"((?:(?<=\D)\.(?=\D))|\n)", re.DOTALL)


def tokens_to_sentences(input: Iterator[str]) -> Iterator[str]:
    buf = ""
    for token in input:
        buf += token
        splits = SEP.split(buf, maxsplit=1)
        if len(splits) == 1:
            continue
        assert len(splits) == 3
        buf = splits.pop()
        if (sentence := "".join(splits[:2]).strip()):
            yield sentence
    if (sentence := buf.strip()):
        yield sentence
