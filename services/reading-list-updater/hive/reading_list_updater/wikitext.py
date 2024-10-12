import re

from typing import Optional
from urllib.parse import unquote


def format_reading_list_entry(
        timestamp: str,
        link: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
) -> str:
    """Generate wikitext for a reading list entry.
    """
    entry = _format_reading_list_entry(link, title)
    entry = f"{{{{at|{timestamp}}}}} {entry}"
    if notes:
        entry = f"{entry} {notes}"
    return entry


# Everything below here is more-or-less verbatim from
# https://github.com/gbenson/hivebot/blob/main/scripts/userscripts/readinglist.py

REWRITES = (
    (r"^https?://en\.(m\.)?wikipedia\.org/wiki/", "wikipedia:"),
    (r"^https?://youtu\.be/", "https://www.youtube.com/watch?v="),
    (r"\?igshid=[a-z0-9+/]*={0,2}", ""),
)


def _format_reading_list_entry(
        entry: str,
        subject: Optional[str] = None,
):
    if entry.split(":", 1)[0] not in {"http", "https"}:
        raise ValueError(entry)

    for pattern, repl in REWRITES:
        entry = re.sub(pattern, repl, entry, 1, re.I)

    if entry.startswith("wikipedia:"):
        entry = unquote(entry).replace("_", " ")
        entry = "[[%s]]" % entry
        if subject:
            entry = "%s ''<q>%s</q>''" % (entry, subject)

    elif subject:
        entry = "%s %s" % (entry, subject)
        if "[" not in entry and "]" not in entry:
            entry = "[%s]" % entry

    return entry
