import logging

from argparse import ArgumentParser
from dataclasses import dataclass, field
from email.utils import formatdate
from typing import Optional

from hive import messaging as msgbus


@dataclass
class ReadingListEntry:
    url: str
    title: Optional[str] = None
    text: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: formatdate(localtime=True))

    @property
    def wikitext(self):
        result = self.url
        if self.title:
            result = f"[{result} {self.title}]"
        if self.text:
            result = f"{result} {self.text}"
        return result

    def as_dict(self):
        return dict(
            (attr, getattr(self, attr))
            for attr in ("timestamp", "wikitext"))


def main():
    parser = ArgumentParser(
        description="Share a link to Hive's reading list.",
    )
    parser.add_argument(
        "url", metavar="URL", help="link to share")
    parser.add_argument(
        "text", metavar="TEXT", nargs="?",
        help="text from the linked page")
    parser.add_argument(
        "-t", "--title", help="title of the linked page")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="increase verbosity (up to -vvv)")
    args = parser.parse_args()

    if (verbosity := args.verbose):
        logging.basicConfig(level={
            1: logging.WARNING,
            2: logging.INFO,
        }.get(verbosity, logging.DEBUG))

    entry = ReadingListEntry(
        args.url,
        title=args.title,
        text=args.text,
    )

    msgbus.send_to_queue("reading_list.updates.outgoing", entry.as_dict())
