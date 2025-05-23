import logging

from typing import Optional

from .entry import ReadingListEntry

logger = logging.getLogger(__name__)


def maybe_decorate_entry(entry: ReadingListEntry, og: dict[str, str]) -> None:
    if (url := og.get("url")) and (
            url != entry.url and not entry.url.startswith(f"{url}#")):
        logger.warning("og:url %r != shared link URL %r", url, entry.url)
    if (title := og.get("title")):
        _maybe_update_title(entry, title)
    if entry.title and (site_name := og.get("site_name")):
        if site_name not in entry.title:
            entry.title = f"{entry.title} | {site_name}"


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
