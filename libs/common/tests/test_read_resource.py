from hive.common import read_resource


def test_read_resource():
    with open(__file__) as fp:
        expected = fp.read()
    result = read_resource("test_read_resource.py")
    assert result == expected
