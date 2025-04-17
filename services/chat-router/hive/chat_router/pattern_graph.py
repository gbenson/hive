from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from functools import cached_property
from typing import Callable, Optional, Sequence, TypeAlias

from .spellchecker import spellcheck
from .tokenizer import Token

Handler: TypeAlias = Callable[[], None]


@dataclass
class Node:
    """A node in a pattern graph.
    """
    children: dict[str, Node] = field(default_factory=dict)
    _handler: Optional[Handler] = None

    @property
    def handler(self) -> Optional[Handler]:
        if (handler := self._handler):
            return handler
        # Cope if the final pattern element is a zero+ wildcard
        # that didn't match anything.
        return getattr(self.children.get("^"), "_handler", None)

    @handler.setter
    def handler(self, handler: Handler) -> None:
        if self._handler:
            raise KeyError
        self._handler = handler

    def add_route(self, tokens: Sequence[str], handler: Handler) -> None:
        if not tokens:
            self.handler = handler
            return

        next_token = tokens[0]
        child = self.children.get(next_token)
        if not child:
            child = type(self)()
            self.children[next_token] = child
        child.add_route(tokens[1:], handler)

    def __str__(self) -> str:
        result = []
        self._describe_into(result)
        return "\n".join(result)

    def _describe_into(
            self,
            result: list[str],
            pattern: tuple[str] = (),
            indent: str = "  ",
    ) -> None:
        if pattern:
            line = f"{indent * len(pattern)}{pattern[-1]}:"
            if self.handler:
                line = f"{line} <handler id=0x{id(self.handler):x}>"
            result.append(line)
        elif self.handler:
            raise ValueError
        else:
            result.append("$:")
        for token, child in sorted(self.children.items()):
            child._describe_into(result, pattern + (token,), indent)


@dataclass
class Candidate:
    node: Node
    token_index: int
    matched_tokens: tuple[Token] = ()
    parent: Optional[Candidate] = None
    is_wildcard: bool = False

    @cached_property
    def pattern(self) -> str:
        """Pattern substring matched by this candidate.
        """
        if not (parent := self.parent):
            return "<|root|>"
        children = parent.node.children
        our_node = self.node
        results = [
            text
            for text, child in children.items()
            if child is our_node
        ]
        assert len(results) == 1
        return results[0]

    def __repr__(self) -> str:
        return f"|{self.pattern}|"


@dataclass
class Span:
    _c: Candidate

    @property
    def is_wildcard(self) -> bool:
        return self._c.is_wildcard

    @property
    def pattern(self) -> str:
        """Pattern substring this span consumed.
        """
        return self._c.pattern

    @property
    def matched_tokens(self) -> tuple[Token]:
        """Normalized input tokens this span consumed.
        """
        return self._c.matched_tokens

    @property
    def match(self) -> str:
        """Normalized input substring this span consumed.
        """
        return " ".join(t.text for t in self.matched_tokens)

    def __repr__(self) -> str:
        p, m = p_m = self.pattern, self.match
        return repr(m if m == p else p_m)


@dataclass
class Match:
    tokens: tuple[Token]
    _c: Candidate

    @property
    def handler(self) -> Handler:
        return self._c.node.handler

    @property
    def match(self) -> str:
        return " ".join(t.text for t in self.tokens)

    @property
    def pattern(self) -> str:
        return " ".join(s.pattern for s in self.spans)

    @property
    def groups(self) -> tuple[Span]:
        return tuple(s for s in self.spans if s.is_wildcard)

    @cached_property
    def spans(self) -> tuple[Span]:
        result = []
        c = self._c
        while (p := c.parent):
            result.insert(0, Span(c))
            c = p
        return tuple(result)

    def __repr__(self) -> str:
        groups = [g.match for g in self.groups]
        return f"Match(pattern={self.pattern!r}, groups={groups!r})"


@dataclass(repr=False)
class Matcher:
    graph: Node
    tokens: tuple[Token]
    matches: list[Match] = field(default_factory=list)

    @property
    def best_match(self) -> Match:
        return max(
            (len(match.pattern) - len(match.groups), -index, match)
            for index, match in enumerate(self.matches)
        )[2]

    def __str__(self) -> str:
        return str(self.matches)

    def __post_init__(self) -> None:
        self._backtrack(self._root())

    # https://en.wikipedia.org/wiki/Backtracking#Pseudocode
    def _backtrack(self, c: Candidate) -> None:
        if self._reject(c):
            return
        if self._accept(c):
            self._output(c)
        for s in self._extensions(c):
            self._backtrack(s)

    def _root(self) -> Candidate:
        """Return the partial candidate at the root of the search tree.
        """
        return Candidate(self.graph, 0)

    def _reject(self, c: Candidate) -> bool:
        """Return True only if the partial candidate c is not worth completing.
        """
        return False  # XXX this reduces the algorithm to brute force

    def _accept(self, c: Candidate) -> bool:
        """Return True if c is a routed full match, otherwise return False.
        """
        if c.token_index != len(self.tokens):
            return False  # the entire input wasn't consumed.
        if not c.node.handler:
            return False  # the node we reached isn't a route.
        return True

    def _output(self, c: Candidate) -> None:
        """Add the solution c of P to the set of valid matches.
        """
        assert c.token_index == len(self.tokens)
        assert c.node.handler
        self.matches.append(Match(self.tokens, c))

    def _extensions(self, c: Candidate) -> Iterator[Candidate]:
        """Iterate over the extensions of candidate c.
        """
        token_index = c.token_index
        if token_index >= len(self.tokens):
            return

        children = c.node.children
        if (s_token := self._get_word_match(token_index, children)):
            s, token = s_token
            yield Candidate(s, token_index + 1, [token], c, False)

        for wildcard in "^*":
            if not (s := children.get(wildcard)):
                continue

            # match_start is the index of the first token of user input
            # the wildcard could consume.
            match_start = token_index

            min_match_limit = match_start + {"^": 0, "*": 1}[wildcard]
            max_match_limit = len(self.tokens)

            match_limits = range(min_match_limit, max_match_limit + 1)
            match_limits = reversed(match_limits)  # reversed makes it greedy

            for match_limit in match_limits:
                match_tokens = self.tokens[match_start:match_limit]
                yield Candidate(s, match_limit, match_tokens, c, True)

    def _get_word_match(
            self,
            token_index: int,
            children: dict[str, Node],
    ) -> Optional[tuple[Candidate, Token]]:
        """Return the candidate and token for a word match.
        """
        token = self.tokens[token_index]
        word = token.text

        if (s := children.get(word)):
            return s, token  # exact match

        if len(word) < 3:
            return None

        candidates = spellcheck.candidates(word)
        if not candidates:
            return None

        candidates &= children.keys()
        if len(candidates) != 1:
            return None

        word = candidates.pop()
        return children.get(word), token.with_text(word)


class PatternGraph(Node):
    def match(self, tokens: Iterable[Token]) -> Optional[Matcher]:
        m = Matcher(self, tuple(tokens))
        return m if len(m.matches) else None
