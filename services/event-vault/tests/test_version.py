from hive.common.testing import assert_is_valid_version
from hive.event_vault.__version__ import __version__


def test_version():
    assert_is_valid_version(__version__)
