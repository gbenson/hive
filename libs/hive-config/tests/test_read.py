import os

import pytest

from hive.config import DEFAULT_READER, read as read_config


def test_not_found():
    with pytest.raises(KeyError):
        read_config("should-not-exist")


@pytest.mark.parametrize(
    "ext", (".json", ".yml.json", ".yaml.json", ".xyz.json"))
def test_read_json(test_config_dir, ext):
    key = write_file(test_config_dir, ext, '{"hello": "world"}')
    assert read_config(key) == {"hello": "world"}


@pytest.mark.parametrize(
    "ext", ("", ".yml", ".yaml", ".json.yml", ".xyz"))
def test_read_yaml(test_config_dir, ext):
    key = write_file(test_config_dir, ext, "hello:\n  world")
    assert read_config(key) == {"hello": "world"}


@pytest.fixture
def test_config_dir(tmp_path, monkeypatch):
    dirname = str(tmp_path)
    with monkeypatch.context() as m:
        m.setattr(DEFAULT_READER, "search_path", [dirname])
        yield dirname


def write_file(dirname, ext, content, basename="config"):
    basename += ext
    with open(os.path.join(dirname, basename), "w") as fp:
        fp.write(content)
    if not ext:
        return basename
    new_basename, ext = os.path.splitext(basename)
    if ext not in DEFAULT_READER.search_exts:
        return basename
    return new_basename
