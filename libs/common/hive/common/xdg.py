import os

from pathlib import Path


def user_config_dir() -> Path:
    """Base directory for user-specific configuration files.

    - Definition: https://specifications.freedesktop.org/basedir-spec/latest/
    - Equivalent: https://pkg.go.dev/os#UserConfigDir
    """
    return _xdg_userdir_for("config")


def user_cache_dir() -> Path:
    """Base directory for user-specific non-essential (cached) data.

    - Definition: https://specifications.freedesktop.org/basedir-spec/latest/
    - Equivalent: https://pkg.go.dev/os#UserCacheDir
    """
    return _xdg_userdir_for("cache")


def _xdg_userdir_for(what: str) -> Path:
    dirname = os.environ.get(f"XDG_{what.upper()}_HOME")
    if dirname:
        return Path(dirname)
    return Path.home() / f".{what}"
