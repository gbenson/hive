import os

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

from hive.email import EmailMessage
from hive.reading_list_updater.entry import ReadingListEntry


@pytest.mark.parametrize(
    ("testcase", "expect_url", "expect_timestamp"),
    (("shl-url-only",
      "https://platform.openai.com/docs/guides/function-calling",
      datetime(2024, 9, 27, 15, 0, 17)),
     ("shl-long-url-only",
      "https://www.reddit.com/r/LocalLLaMA/comments/18ljvxb/"
      "llm_prompt_format_comparisontest_mixtral_8x7b/?rdt=49183",
      datetime(2024, 9, 27, 10, 10, 8)),
     ))
def test_link_only(testcase, expect_url, expect_timestamp):
    entry = ReadingListEntry.from_email_summary(
        read_email_summary_resource(testcase))
    assert entry.url == expect_url
    assert entry.title is None
    assert entry.notes is None
    assert entry.timestamp == format_datetime(expect_timestamp)


@pytest.mark.parametrize(
    ("testcase", "expect_url", "expect_title", "expect_notes",
     "expect_timestamp"),
    (("k9-url+subject+long-excerpt",
      "https://docs.python.org/3/library/asyncio-task.html#creating-tasks",
      "Event loop only stores weak references to tasks",
      "Important Save a reference to the result of this function, to"
      " avoid a task disappearing mid-execution. The event loop only"
      " keeps weak references to tasks. A task that isn\u2019t refer"
      "enced elsewhere may get garbage collected at any time, even b"
      "efore it\u2019s done. For reliable \u201cfire-and-forget\u201d"
      " background tasks, gather them in a collection:",
      datetime(2024, 9, 25, 8, 55, 47, tzinfo=timezone(timedelta(hours=1)))),
     ("k9-long-url+subject+excerpt",
      "https://stackoverflow.com/questions/72897924/python-rabbitmq-"
      "pika-consumer-how-to-use-async-function-as-callback#72902709",
      "Python call async from sync",
      "I annotated my callback with @sync where sync is...",
      datetime(2024, 9, 25, 8, 54, 5, tzinfo=timezone(timedelta(hours=1)))),
     ))
def test_full_monty(
        testcase,
        expect_url,
        expect_title,
        expect_notes,
        expect_timestamp,
):
    entry = ReadingListEntry.from_email_summary(
        read_email_summary_resource(testcase))
    assert entry.url == expect_url
    assert entry.title == expect_title
    assert entry.notes == expect_notes
    assert entry.timestamp == format_datetime(expect_timestamp)


# Helpers

def read_email_resource(basename: str) -> bytes:
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "resources", f"{basename}.eml")
    with open(filename, "rb") as fp:
        return fp.read()


def read_email_summary_resource(basename: str) -> dict[str, str]:
    return EmailMessage.from_bytes(read_email_resource(basename)).summary
