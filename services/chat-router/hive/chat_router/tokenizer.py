from __future__ import annotations

import re

from collections.abc import Iterable
from itertools import chain
from dataclasses import asdict, dataclass, field

WORD_RE = re.compile(r"(\w+)")


@dataclass(frozen=True)
class Token:
    source: str = field(compare=False)
    start: int
    limit: int
    text: str
    starts_word: bool

    def __post_init__(self) -> None:
        if " " in self.text:
            raise ValueError  # pragma: no cover
        if self.start < 0:
            raise ValueError  # pragma: no cover
        if self.limit < self.start:
            raise ValueError  # pragma: no cover
        if len(self.source) < self.limit:
            raise ValueError  # pragma: no cover

    @classmethod
    def from_string(
            cls,
            s: str,
            start: int = 0,
            limit: int = -1,
            starts_word: bool = True,
    ) -> Token:
        """Create a token from `s[start:limit]`.
        """
        if limit == -1:
            limit = len(s)
        if start < 0:
            raise ValueError
        if limit <= start:
            raise ValueError
        if len(s) < limit:
            raise ValueError

        return cls(s, start, limit, s[start:limit], starts_word)

    def with_text(self, text: str) -> Token:
        """Return a token with the given text at this token's alignment.
        """
        if text == self.text:
            return self
        return self.with_values(text=text)

    def with_values(self, **kwargs) -> Token:
        """Return a token with some attributes updated.
        """
        old_kwargs = asdict(self)
        new_kwargs = old_kwargs.copy()
        new_kwargs.update(kwargs)
        if new_kwargs == old_kwargs:
            return self
        return type(self)(**new_kwargs)

    @property
    def source_text(self) -> str:
        return self.source[self.start:self.limit]


def tokenize(s: str) -> Iterable[Token]:
    """Split a string into normalized tokens.
    """
    tokens = split(s)
    tokens = map(casefold, tokens)
    tokens = chain.from_iterable(split_words(t) for t in tokens)
    tokens = disabbreviate(tokens)
    tokens = chain.from_iterable(expand(t) for t in tokens)
    return tokens


def split(s: str) -> Iterable[Token]:
    """Split a string into whitespace-separated tokens.
    """
    start = 0
    for word in s.split():
        start = s.find(word, start)
        if start < 0:
            raise RuntimeError  # pragma: no cover
        limit = start + len(word)
        yield Token.from_string(s, start, limit)
        start = limit


def casefold(token: Token) -> Token:
    """Return a version of the token suitable for caseless comparison.
    """
    return token.with_text(APOSTROPHISH_RE.sub("'", token.text.casefold()))


def split_words(token: Token) -> Iterable[Token]:
    """Split a token into a word- and non-word sections.
    """
    s = token.text

    # Make it break on "_" but not on "'"
    ss = s.replace("_", " ").replace("'", "_")

    start = token.start
    starts_word = True
    for i, tt in enumerate(WORD_RE.split(ss)):
        is_sep = not bool(i & 1)
        if not tt:
            assert is_sep
            continue

        # Undo the previous transformation
        t = tt.replace("_", "'").replace(" ", "_")

        if t == s:
            yield token
            return

        ts = list(t) if is_sep else [t]
        for t in ts:
            limit = start + len(t)
            yield token.with_values(
                text=t,
                start=start,
                limit=limit,
                starts_word=starts_word,
            )
            start = limit
        starts_word = False


def disabbreviate(tokens: Iterable[Token]) -> Iterable[Token]:
    """Normalize abbreviations.
    """
    tokens = map(_disabbreviate_direct, tokens)
    word_break = False
    for token in tokens:
        s = token.text
        t = WHITESPACE_MODIFYING_ABBREVIATIONS.get(s, s)
        text_changed = t != s
        if text_changed or word_break:
            token = token.with_values(text=t, starts_word=True)
            word_break = text_changed
        yield token


def _disabbreviate_direct(token: Token) -> Token:
    """Normalize abbreviations that don't modify whitespace.
    """
    s = token.text
    if not (t := DIRECT_ABBREVIATIONS.get(s)):
        return token
    return token.with_text(t)


def expand(token: Token) -> Iterable[Token]:
    """Expand standard contractions.
    """
    s = token.text
    t = EXPANSIONS.get(s, s)
    if t == s:
        yield token
        return

    t, u = t.split()
    if s.startswith(t):
        split = token.start + len(t)
    elif u in ("not", "to"):
        split = token.limit - len(u)
    else:
        raise ValueError  # pragma: no cover

    yield token.with_values(text=t, limit=split, starts_word=True)
    yield token.with_values(text=u, start=split, starts_word=True)


APOSTROPHISH_CODEPOINTS = {
    0x02b9,  # Modifier letter prime
    0x02bc,  # Modifier letter apostrophe
    0x02bf,  # Modifier letter left half ring
    0x02c8,  # Modifier letter vertical line
    0x055a,  # Armenian apostrophe
    0x05f3,  # Hebrew punctuation geresh
    0x1fbd,  # Greek koronis
    0x1fbf,  # Greek psili
    0x1ffd,  # Greek oxia
    0x2018,  # Left single quotation mark
    0x2019,  # Right single quotation mark
    0x201b,  # Single high-reversed-9 quotation mark
    0x2032,  # Prime
    0x275c,  # Heavy single comma quotation mark ornament
    0xff07,  # Fullwidth apostrophe
}
APOSTROPHISH_CHARACTERS = "".join(map(chr, sorted(APOSTROPHISH_CODEPOINTS)))
APOSTROPHISH_RE = re.compile(rf"[{APOSTROPHISH_CHARACTERS}]")

ABBREVIATIONS = dict(
    line.split()
    for line in """
        &       and
        +       and
        /       or
        passwd  password
        pls     please
        u       you
        ur      your
    """.strip().split("\n")
)
DIRECT_ABBREVIATIONS = dict(
    (_in, out)
    for _in, out in ABBREVIATIONS.items()
    if _in.isalnum()
)
WHITESPACE_MODIFYING_ABBREVIATIONS = dict(
    (_in, out)
    for _in, out in ABBREVIATIONS.items()
    if _in not in DIRECT_ABBREVIATIONS
)

# Standard (and non-standard!) English contractions
#
# N.B. Some of these have more than one expansion:
#  - Many "X'd" could be "X would" or "X had",
#    and others could be "X would" or "X did".
#    I've mostly preferred did over would, and would over had.
#  - Many "X's" could be "X is" or "X has",
#    and "what's" could additionally be "what does";
#    all are expanded to the "X is" form here.
#
# The list is long, and can likely be trimmed once I have
# some patterns and can see what's useful and what isn't.
EXPANSIONS = dict(
    line.lower().split(maxsplit=1)
    for line in """
        ain't         is not
        aren't        are not
        can't         can not
        cannot        can not
        couldn't      could not
        could've      could have
        didn't        did not
        don't         do not
        gonna         going to
        hadn't        had not
        hasn't        has not
        haven't       have not
        he'd          he would
        he'll         he will
        here's        here is
        he's          he is
        how's         how is
        I'd           I would
        I'll          I will
        I'm           I am
        isn't         is not
        it'd          it would
        it'll         it will
        it's          it is
        I've          I have
        let's         let us
        mightn't      might not
        might've      might have
        mustn't       must not
        must've       must have
        needn't       need not
        nobody's      nobody is
        nothing's     nothing is
        one's         one is
        oughtn't      ought not
        shan't        shall not
        she'd         she would
        she'll        she will
        she's         she is
        shouldn't     should not
        should've     should have
        somebody's    somebody is
        someone's     someone is
        something's   something is
        that'd        that would
        that's        that is
        that've       that have
        there'd       there would
        there'll      there will
        there's       there is
        they'd        they would
        they'll       they will
        they're       they are
        they've       they have
        wanna         want to
        wasn't        was not
        we'd          we would
        we'll         we will
        weren't       were not
        we're         we are
        we've         we have
        what'd        what did
        what'll       what will
        what're       what are
        what's        what is
        when'd        when did
        when'll       when will
        when's        when is
        where'd       where did
        where'll      where will
        where's       where is
        which've      which have
        who'd         who would
        who'll        who will
        who're        who are
        who'd         who did
        who's         who is
        who've        who have
        why'd         why did
        why'll        why will
        why's         why is
        won't         will not
        wouldn't      would not
        would've      would have
        you'd         you would
        you'll        you will
        you're        you are
        you've        you have
    """.strip().split("\n")
)
