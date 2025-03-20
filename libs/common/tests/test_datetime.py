from datetime import datetime, timedelta, timezone

import pytest

from hive.common import parse_datetime, utc_now


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


def test_utc_now():
    naive_datetime = datetime.now()
    aware_datetime = parse_datetime("2025-03-20T01:28:41.528744-07:00")
    aware_now = utc_now()

    delta = (aware_now - aware_datetime).total_seconds()
    assert delta > 3600
    assert ((aware_datetime - aware_now).total_seconds() + delta) < 1e-9

    with pytest.raises(TypeError):
        _ = aware_now - naive_datetime
    with pytest.raises(TypeError):
        _ = naive_datetime - aware_now
