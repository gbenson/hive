from datetime import timedelta

import pytest

from hive.common import units


def test_names():
    assert {attr for attr in dir(units) if attr[0].isupper()} == {
        "BYTE", "KiB", "MiB", "GiB", "TiB",
        "SECOND", "MINUTE", "HOUR", "DAY",
        "MILLISECOND", "MICROSECOND",
    }


@pytest.mark.parametrize(
    "attr,expect_value",
    (("BYTE", 1),
     ("GiB", 1_073_741_824),
     ("KiB", 1024),
     ("MiB", 1_048_576),
     ("TiB", 1099511627776),
     ))
def test_integers(attr, expect_value):
    value = getattr(units, attr)
    assert isinstance(value, int)
    assert value == expect_value


@pytest.mark.parametrize(
    "attr,expect_value",
    (("DAY", 86400),
     ("HOUR", 3600),
     ("MICROSECOND", 1e-6),
     ("MILLISECOND", 0.001),
     ("MINUTE", 60),
     ("SECOND", 1),
     ))
def test_timedeltas(attr, expect_value):
    value = getattr(units, attr)
    assert isinstance(value, timedelta)
    assert value.total_seconds() == expect_value
