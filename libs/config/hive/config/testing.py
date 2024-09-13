import pytest

from . import DEFAULT_READER


@pytest.fixture
def test_config_dir(tmp_path, monkeypatch):
    dirname = str(tmp_path)
    with monkeypatch.context() as m:
        m.setattr(DEFAULT_READER, "search_path", [dirname])
        yield dirname
