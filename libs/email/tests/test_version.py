import pytest

from hive.email.__version__ import __version__
try:
    from hive.common.testing import assert_is_valid_version
except ModuleNotFoundError:
    assert_is_valid_version = None


@pytest.mark.skipif(
    assert_is_valid_version is None,
    reason="hive.common not installed")
def test_version():
    assert_is_valid_version(__version__)
