import logging

from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from hishel import CacheClient

from .entry import ReadingListEntry

logger = logging.getLogger(__name__)


def maybe_decorate_entry(entry: ReadingListEntry) -> None:
    client = CacheClient(http2=True)

    cf = Path(__file__)
    ua = ["https://github.com/gbenson/hive/blob/main", cf.name]
    for pp in cf.parents[:5]:
        ua.insert(1, pp.name)
    client.headers["user-agent"] = f"HiveBot (bot; +{'/'.join(ua)})"

    try:
        response = client.get(entry.url)
        soup = BeautifulSoup(response.text, "lxml")
        _maybe_decorate_entry(entry, soup)

    except Exception:
        logger.warning("EXCEPTION", exc_info=True)
        raise


def _maybe_decorate_entry(
        entry: ReadingListEntry,
        soup: BeautifulSoup,
) -> None:
    for tag in soup.find_all("meta"):
        match tag.get("property"):
            case "og:url":
                if (og_url := tag.get("content")) != entry.url:
                    logger.warning("og:url %r != %r", og_url, entry.url)
            case "og:title":
                _maybe_update_title(entry, tag.get("content"))
                return


def _maybe_update_title(entry: ReadingListEntry, title: Optional[str]) -> None:
    if not title:
        return
    if not entry.title:
        entry.title = title
        return
    if title in entry.title:
        entry.title = title  # shorter == better?
        return
    if entry.title.endswith("..."):
        if title.startswith(entry.title.removesuffix("...")):
            entry.title = title
            return
    logger.warning("og:title %r != %r", title, entry.title)
