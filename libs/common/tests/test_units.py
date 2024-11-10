from hive.common import units


def test_units():
    assert (
        ("BYTE", 1),
        ("BYTES", 1),
        ("DAY", 86400),
        ("DAYS", 86400),
        ("GiB", 1_073_741_824),
        ("HOUR", 3600),
        ("HOURS", 3600),
        ("KiB", 1024),
        ("MICROSECOND", 1e-6),
        ("MICROSECONDS", 1e-6),
        ("MILLISECOND", 0.001),
        ("MILLISECONDS", 0.001),
        ("MINUTE", 60),
        ("MINUTES", 60),
        ("MiB", 1_048_576),
        ("SECOND", 1),
        ("SECONDS", 1),
        ("TiB", 1099511627776),
    ) == tuple(
        (attr, getattr(units, attr))
        for attr in sorted(dir(units))
        if attr[0].isupper()
    )
