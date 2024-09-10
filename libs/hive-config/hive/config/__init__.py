import json
import os
import yaml

from typing import Optional
from collections.abc import Iterable


def user_config_dir() -> Optional[str]:
    """https://pkg.go.dev/os#UserConfigDir"""
    dirname = os.environ.get("XDG_CONFIG_HOME")
    if dirname:
        return dirname
    homedir = os.environ.get("HOME")
    if homedir:
        return os.path.join(homedir, ".config")
    return None


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
            ".env",
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
        if ext in {"env", "json"}:
            type = ext
        return getattr(self, f"_read_{type}")(filename)

    def _read_env(self, filename):
        with open(filename) as fp:
            lines = fp.readlines()
        lines = [line.split("#", 1)[0].strip() for line in lines]
        items = [line.split("=", 1) for line in lines if line]
        return dict((k.rstrip(), v.lstrip()) for k, v in items)

    def _read_json(self, filename):
        with open(filename) as fp:
            return json.load(fp)

    def _read_yaml(self, filename):
        with open(filename) as fp:
            return yaml.safe_load(fp)


DEFAULT_READER = Reader()

read = DEFAULT_READER.read
