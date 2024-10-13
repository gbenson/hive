import re

WORD_RE = re.compile(r"\w+")


def words_for_bag(text: str) -> list[str]:
    return [
        word
        for word in WORD_RE.findall(text.lower())
        if 3 < len(word) <= 12
        and word.isalpha()
    ]


def bag_of_words(text: str) -> set[str]:
    return set(words_for_bag(text))
