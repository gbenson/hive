from pathlib import Path

import pytest

from hive.common import user_cache_dir, user_config_dir


@pytest.mark.parametrize(
    "func,xdgvar",
    ((user_cache_dir, "XDG_CACHE_HOME"),
     (user_config_dir, "XDG_CONFIG_HOME"),
     ))
def test_with_xdg_var(func, xdgvar, monkeypatch):
    monkeypatch.setenv(xdgvar, "/xdg/magic/beans/")
    assert func() == Path("/xdg/magic/beans")


@pytest.mark.parametrize(
    "func,xdgvar,expect_path",
    ((user_cache_dir, "XDG_CACHE_HOME", Path("/eatme/.cache/")),
     (user_config_dir, "XDG_CONFIG_HOME", Path("/eatme/.config")),
     ))
def test_without_xdg_var(func, xdgvar, monkeypatch, expect_path):
    monkeypatch.delenv(xdgvar, raising=False)
    monkeypatch.setenv("HOME", "/eatme")
    assert func() == expect_path
