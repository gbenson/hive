import pytest

from pathlib import Path
from typing import Iterable

try:
    from pep440_version_utils import Version  # type: ignore
except ImportError:  # pragma: no cover
    pass

from .config import DEFAULT_READER


def assert_is_valid_version(version: str) -> None:
    try:
        assert str(Version(version)) == version
    except Exception as e:
        raise AssertionError(f"Invalid version {version!r}") from e


@pytest.fixture
def test_config_dir(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
) -> Iterable[str]:
    dirname = str(tmp_path)
    with monkeypatch.context() as m:
        m.setattr(DEFAULT_READER, "search_path", [dirname])
        yield dirname


def want_to_see(caplog: pytest.LogCaptureFixture, msg: str) -> None:
    failure_detail = f"didn't see: {msg}"
    assert any(r.getMessage() == msg for r in caplog.records), failure_detail
