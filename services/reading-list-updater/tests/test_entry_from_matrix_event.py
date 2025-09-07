from typing import Any

import pytest

from hive.reading_list_updater.entry import ReadingListEntry


@pytest.fixture
def email_summary() -> dict[str, Any]:
    return {
        "body": (
            "https://python.langchain.com/docs/how_to/#extraction"
            " Extraction is when you use LLMs to extract structured"
            " information from unstructured text."
        ),
        "content_type": "text/plain",
        "created_from": {
            "id": "$7hXAz0FDCNCVUT9fCsK5ILHdfDRGqdvo4WP9BfEHs6I",
            "source": "https://gbenson.net/hive/services/matrix-connector",
            "type": "net.gbenson.hive.matrix_event",
        },
        "date": "Sat, 06 Sep 2025 21:15:05 +0000",
    }


def test_with_matrix_event_id(email_summary: dict[str, Any]) -> None:
    entry = ReadingListEntry.from_email_summary(email_summary)
    assert entry.source_matrix_event_id == (
        "$7hXAz0FDCNCVUT9fCsK5ILHdfDRGqdvo4WP9BfEHs6I")


def test_no_event_source(email_summary: dict[str, Any]) -> None:
    del email_summary["created_from"]
    entry = ReadingListEntry.from_email_summary(email_summary)
    assert entry.source is None
    assert entry.source_matrix_event_id is None


def test_empty_event_source(email_summary: dict[str, Any]) -> None:
    email_summary["created_from"] = {}
    entry = ReadingListEntry.from_email_summary(email_summary)
    assert entry.source is None
    assert entry.source_matrix_event_id is None


def test_wrong_event_type(email_summary: dict[str, Any]) -> None:
    email_summary["created_from"]["type"] += "-NOT"
    entry = ReadingListEntry.from_email_summary(email_summary)
    assert entry.source == email_summary["created_from"]
    assert entry.source is not email_summary["created_from"]
    assert entry.source_matrix_event_id is None
