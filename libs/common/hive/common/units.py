from datetime import timedelta

BYTE = 1
KiB = BYTE << 10
MiB = KiB << 10
GiB = MiB << 10
TiB = GiB << 10

SECOND = timedelta(seconds=1)
MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)

MILLISECOND = timedelta(milliseconds=1)
MICROSECOND = timedelta(microseconds=1)
