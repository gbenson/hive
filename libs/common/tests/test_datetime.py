from datetime import datetime, timedelta, timezone

import pytest

from hive.common import parse_datetime


# These are the examples from
# https://docs.python.org/3.13/library/datetime.html#datetime.datetime.fromisoformat
@pytest.mark.parametrize(
    "date_string,expect_result",
    (("2011-11-04",
      datetime(2011, 11, 4, 0, 0)),
     #("20111104",
     # datetime(2011, 11, 4, 0, 0)),
     ("2011-11-04T00:05:23",
      datetime(2011, 11, 4, 0, 5, 23)),
     ("2011-11-04T00:05:23Z",
      datetime(2011, 11, 4, 0, 5, 23, tzinfo=timezone.utc)),
     #("20111104T000523",
     # datetime(2011, 11, 4, 0, 5, 23)),
     #("2011-W01-2T00:05:23.283",
     # datetime(2011, 1, 4, 0, 5, 23, 283000)),
     ("2011-11-04 00:05:23.283",
      datetime(2011, 11, 4, 0, 5, 23, 283000)),
     ("2011-11-04 00:05:23.283+00:00",
      datetime(2011, 11, 4, 0, 5, 23, 283000, tzinfo=timezone.utc)),
     ("2011-11-04T00:05:23+04:00",
      datetime(2011, 11, 4, 0, 5, 23,
               tzinfo=timezone(timedelta(seconds=14400)))),
     ("2011-11-04T00:05:23Z",
      datetime(2011, 11, 4, 0, 5, 23, tzinfo=timezone.utc)),
     ))
def test_parse_datetime(date_string, expect_result):
    assert parse_datetime(date_string) == expect_result
