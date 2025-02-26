import logging

from collections.abc import Iterator

from bs4 import BeautifulSoup

from hive.common import httpx

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


def opengraph_properties(url: str, prefix: str = "og:") -> dict[str, str]:
    props = dict(_opengraph_props(url, prefix))
    d("Opengraph properties: %r", props)
    return props


def _opengraph_props(url: str, prefix: str) -> Iterator[tuple[str, str]]:
    r = httpx.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    for tag in soup.find_all("meta"):
        if not (name := tag.get("property")):
            continue
        if not name.startswith(prefix):
            continue
        yield name.removeprefix(prefix), tag.get("content")
