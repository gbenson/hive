import pytest

from hive.common.testing import assert_is_valid_version


@pytest.mark.parametrize(
    "invalid_version",
    (("1.2-3"),
     ("1.2-3-final"),
     ))
def test_is_valid_version(invalid_version):
    with pytest.raises(AssertionError):
        assert_is_valid_version(invalid_version)
