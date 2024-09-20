try:
    from pep440_version_utils import Version
except ImportError:
    pass


def assert_is_valid_version(version: str):
    try:
        assert str(Version(version)) == version
    except Exception as e:
        raise AssertionError(f"Invalid version {version!r}") from e


def want_to_see(caplog, msg):
    failure_detail = f"didn't see: {msg}"
    assert any(r.getMessage() == msg for r in caplog.records), failure_detail
