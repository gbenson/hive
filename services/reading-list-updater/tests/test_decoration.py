import pytest

from hive.reading_list_updater.entry import ReadingListEntry
from hive.reading_list_updater.service import Service


class MockChannel:
    def maybe_publish_event(self, **kwargs):
        pass


@pytest.mark.parametrize("update_request,expect_json,expect_wikitext", (({
    # Shared via shl
    "date": "Tue, 25 Feb 2025 19:43:50 +0000",
    "from": NotImplemented,
    "body": "https://en.wikipedia.org/wiki/Roguelike",
}, {
    "timestamp": "Tue, 25 Feb 2025 19:43:50 +0000",
    "url": "https://en.wikipedia.org/wiki/Roguelike",
    "title": "Roguelike - Wikipedia",
}, (
    "{{at|Tue, 25 Feb 2025 19:43:50 +0000}} "
    "[[wikipedia:Roguelike]]"
)),))
def test_wikipedia(update_request, expect_json, expect_wikitext):
    entry = ReadingListEntry.from_email_summary(update_request)
    Service().maybe_decorate_entry(MockChannel(), entry)

    assert entry.url == "https://en.wikipedia.org/wiki/Roguelike"

    if not entry.title:
        pytest.skip("No internet?")

    # The decorator added a (pointless) title.
    assert entry.json() == expect_json

    # The pointless title didn't end up in the wikitext.
    assert entry.as_wikitext() == expect_wikitext


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
def test_youtube(update_request):
    entry = ReadingListEntry.from_email_summary(update_request)
    original_title = entry.title
    Service().maybe_decorate_entry(MockChannel(), entry)

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


@pytest.mark.parametrize("update_request", ({
    "meta": NotImplemented,
    "date": "Fri, 28 Feb 2025 23:58:29 +0000",
    "body": "https://www.youtube.com/shorts/_N39UWtPK9k",
},))
def test_youtube_short(update_request):
    entry = ReadingListEntry.from_email_summary(update_request)
    original_title = entry.title
    Service().maybe_decorate_entry(MockChannel(), entry)

    assert entry.url == "https://www.youtube.com/watch?v=_N39UWtPK9k"

    if entry.title == original_title:
        pytest.skip("No internet?")

    expect_title = (
        "Why taxes keep rising but public services keep getting worse"
        " | YouTube"
    )
    assert entry.title == expect_title

    assert entry.json() == {
        "timestamp": "Fri, 28 Feb 2025 23:58:29 +0000",
        "url": "https://www.youtube.com/watch?v=_N39UWtPK9k",
        "title": expect_title,
    }
