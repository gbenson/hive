import logging
import re

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from threading import Lock
from typing import Callable

from ..router import Handler, Router

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Brain(Router):
    def __lazy_init__(self) -> None:
        want_name = re.compile(r"\.[a-z][a-z0-9_]*")
        for path in Path(__file__).parent.glob("*.py"):
            name = f".{path.stem}"
            if not want_name.fullmatch(name):
                continue
            module = import_module(name, __name__)
            d("Imported %s", module.__name__)
            assert module.__file__ == str(path)
            assert module.__name__.endswith(name[1:])

    def add_canned_response(self, pattern: str, response: str) -> None:
        """Add a pattern to elicit a canned response.
        """
        self.add_route(pattern, self.send_text(response))

    def request_llm_response(self) -> Handler:
        """Return a handler that requests an LLM response.
        """
        return self.receive("on_request_llm_response")

    def send_text(self, text: str) -> Handler:
        """Return a handler that sends the given text.
        """
        return self.receive("on_send_text", text)


router = Brain()

add_route = router.add_route
rewrite = router.rewrite
receive = router.receive

add_canned_response = router.add_canned_response
send_text = router.send_text
request_llm_response = router.request_llm_response


def route(
        pattern: str = "",
        patterns: tuple[str] = (),

) -> Callable[[Handler], Handler]:
    """Decorator.
    """
    if bool(pattern) == bool(patterns):
        raise ValueError('need "pattern" or "patterns"')
    if not patterns:
        patterns = (pattern,)

    def decorator(handler: Handler) -> Handler:
        for pattern in patterns:
            router.add_route(pattern, handler)
        return handler

    return decorator


def lstrip(prefix: str) -> None:
    rewrite(f"{prefix} _", "*")


def rstrip(suffix: str) -> None:
    rewrite(f"_ {suffix}", "*")
