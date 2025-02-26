import logging

from collections.abc import Iterator

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


def opengraph_properties(html: str, prefix: str = "og:") -> dict[str, str]:
    props = dict(_opengraph_props(html, prefix))
    d("Opengraph properties: %r", props)
    return props


def _opengraph_props(html: str, prefix: str) -> Iterator[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all("meta"):
        if not (name := tag.get("property")):
            continue
        if not name.startswith(prefix):
            continue
        yield name.removeprefix(prefix), tag.get("content")
