import re

from .youtube import maybe_rewrite_youtube_url


def maybe_rewrite_url(url: str) -> str:
    expr = re.compile(r"maybe_rewrite_\w+_url")
    for name, func in globals().items():
        if expr.fullmatch(name):
            if (rewritten_url := func(url)):
                return rewritten_url
    return url
