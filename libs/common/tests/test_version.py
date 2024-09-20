from hive.common.__version__ import __version__
from hive.common.testing import assert_is_valid_version


def test_version():
    assert_is_valid_version(__version__)
