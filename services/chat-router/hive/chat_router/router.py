from __future__ import annotations

import logging

from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cached_property, partial
from threading import Lock, local as ThreadLocal
from typing import Any

from .pattern_graph import Handler, PatternGraph, Span
from .tokenizer import Token, tokenize

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Router:
    """Routers match tokenized user input against a list of patterns,
    calling the handler for the pattern that most closely matches the
    input.

    Routers are safe for concurrent *dispatch* by multiple threads.
    Modifying the graph is not thread safe, and must be serialized
    by the caller.  Modifying the graph while dispatching is not
    supported.
    """
    _graph: PatternGraph = field(default_factory=PatternGraph)
    request: ThreadLocal = field(default_factory=ThreadLocal)

    def add_route(self, pattern: str, handler: Handler) -> None:
        """Register the handler for the given pattern.
        """
        tokens = pattern.split()
        if not tokens:
            raise ValueError
        self._graph.add_route(tokens, handler)

    def dispatch(self, text: str, receiver: Any, *args, **kwargs) -> None:
        """Dispatch a request to the best matching handler.
        """
        self.request.receiver = receiver
        self.request.args = args
        self.request.kwargs = kwargs
        self.request.text = text
        self.request.tokens = None
        self.request.match = None
        self._dispatch(tokenize(text))

    def _dispatch(self, tokens: Iterable[Token]) -> None:
        tokens = tuple(tokens)
        if not tokens:
            tokens = (Token.from_string("\a"),)
        self.request.tokens = tokens
        self.request.match = None
        d("dispatch: %r", " ".join(t.text for t in tokens))
        if not (matches := self.graph.match(tokens)):
            raise KeyError
        self.request.match = match = matches.best_match
        match.handler()

    _lazy_init_lock: Lock = field(default_factory=Lock, repr=False)

    @cached_property
    def graph(self) -> PatternGraph:
        with self._lazy_init_lock:
            self.__lazy_init__()
        return self._graph

    def __lazy_init__(self) -> None:
        """Override to lazily initialize the pattern graph."""

    def receive(self, method_name: str, *args, **kwargs) -> Handler:
        """Return a handler that invokes the given receiver method.
        """
        return partial(self.call, method_name, *args, **kwargs)

    def call(self, method_name: str, *args, **kwargs) -> Any:
        """Invoke the given receiver method.
        """
        method = getattr(self.request.receiver, method_name)
        method = partial(method, *self.request.args, **self.request.kwargs)
        return method(*args, **kwargs)

    def rewrite(self, pattern: str, template: str) -> None:
        """Register a handler that re-dispatches with replaced input.
        """
        t = Template(tuple(tokenize(template, append_special="#_^*")))
        self.add_route(pattern, partial(self._rewrite, t))

    def _rewrite(self, template: Template) -> None:
        self._dispatch(template.expand(self.request.match.groups))


@dataclass
class Template:
    tokens: tuple[Token]

    def expand(self, subs: Iterable[Span]) -> Iterable[Token]:
        subs = iter(subs)
        for token in self.tokens:
            if token.text != "*":
                yield token
                continue
            sub = next(subs)
            for token in sub.matched_tokens:
                yield token
