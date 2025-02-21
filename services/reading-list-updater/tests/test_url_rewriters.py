import pytest

from hive.reading_list_updater.url_rewriters import maybe_rewrite_url


@pytest.mark.parametrize(
    "original_url,expect_rewritten",
    (("https://www.youtube.com/watch?v=OBkMbPpLCqw",
      "https://www.youtube.com/watch?v=OBkMbPpLCqw"),
     ("http://youtube.com/watch?v=OBkMbPpLCqw&si=aE7WlPsTE6jdQn19",
      "https://www.youtube.com/watch?v=OBkMbPpLCqw"),
     ("https://youtu.be/OBkMbPpLCqw?si=LDz6PQVjCyE_ARAB&t=2",
      "https://www.youtube.com/watch?v=OBkMbPpLCqw&t=2"),
     ))
def test_url_rewriting(original_url: str, expect_rewritten: str) -> None:
    assert maybe_rewrite_url(original_url) == expect_rewritten
