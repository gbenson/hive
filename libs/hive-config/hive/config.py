import json
import os
import yaml

from typing import Optional
from collections.abc import Iterable


def user_config_dir() -> Optional[str]:
    """https://pkg.go.dev/os#UserConfigDir"""
    homedir = os.environ.get("XDG_CONFIG_HOME")
    if not homedir:
        homedir = os.environ.get("HOME")
        if not homedir:
            return None
    return os.path.join(homedir, ".config")


class Reader:
    def __init__(self, subdirs: Iterable[str] = ("gbenson", "hive")):
        self.search_path = [
            os.path.join(dirname, *subdirs)
            for dirname in (user_config_dir(), "/etc")
            if dirname
        ]
        self.search_exts = [
            "",
            ".yml",
            ".yaml",
            ".json",
        ]

    def get_filename_for(self, key: str) -> str:
        for dirname in self.search_path:
            basename = os.path.join(dirname, key)
            for ext in self.search_exts:
                filename = basename + ext
                if os.path.isfile(filename):
                    return filename
        raise KeyError(key)

    def read(self, key: str, type: str = "yaml"):
        filename = self.get_filename_for(key)
        ext = os.path.splitext(filename)[1].lstrip(".")
        if ext == "json":
            type = ext
        return getattr(self, f"_read_{type}")(filename)

    def _read_json(self, filename):
        with open(filename) as fp:
            return json.load(fp)

    def _read_yaml(self, filename):
        with open(filename) as fp:
            return yaml.load(fp, Loader=yaml.Loader)


DEFAULT_READER = Reader()

read = DEFAULT_READER.read
