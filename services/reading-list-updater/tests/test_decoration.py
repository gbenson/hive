import pytest

from hive.reading_list_updater.decoration import maybe_decorate_entry
from hive.reading_list_updater.entry import ReadingListEntry


@pytest.mark.parametrize("update_request", ({
    # Shared via Element
    "meta": NotImplemented,
    "date": "Fri, 21 Feb 2025 09:52:29 +0000",
    "body": "https://youtube.com/watch?v=OBkMbPpLCqw&si=aE7WlPsTE6jdQn19",
}, {
    # Shared via K-9 Mail
    "date": "Fri, 21 Feb 2025 09:52:29 +0000",
    "from": NotImplemented,
    "subject": ("How to Make Small Language Models Work."
                " Yejin Choi Presents at Data + AI..."),
    "message_id": NotImplemented,
    "body": "<https://youtu.be/OBkMbPpLCqw?si=LDz6PQVjCyE_ARAB>",
}))
def test_youtube_decorator(update_request):
    entry = ReadingListEntry.from_email_summary(update_request)
    original_title = entry.title
    maybe_decorate_entry(entry)

    assert entry.url == "https://www.youtube.com/watch?v=OBkMbPpLCqw"

    if entry.title == original_title:
        pytest.skip("No internet?")

    expect_title = (
        "How to Make Small Language Models Work."
        " Yejin Choi Presents at Data + AI Summit 2024 | YouTube"
    )
    assert entry.title == expect_title

    assert entry.json() == {
        "timestamp": "Fri, 21 Feb 2025 09:52:29 +0000",
        "url": "https://www.youtube.com/watch?v=OBkMbPpLCqw",
        "title": expect_title,
    }
