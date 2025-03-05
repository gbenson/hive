import json
import os
import yaml

from collections.abc import Iterable

from .xdg import user_config_dir


class Reader:
    def __init__(self, subdirs: Iterable[str] = ("hive",)):
        self.search_path = [
            os.path.join(dirname, *subdirs)
            for dirname in (user_config_dir(), "/etc")
            if dirname
        ]
        self.search_path.append("/run/secrets")
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
        result = dict((k.rstrip(), v.lstrip()) for k, v in items)
        prefix = os.path.splitext(
            os.path.basename(filename))[0].upper().replace("-", "_") + "_"
        extras = dict(
            (key[len(prefix):].lower(), value)
            for key, value in result.items()
            if key.startswith(prefix)
        )
        extras.update(result)
        return extras

    def _read_json(self, filename):
        with open(filename) as fp:
            return json.load(fp)

    def _read_yaml(self, filename):
        with open(filename) as fp:
            return yaml.safe_load(fp)


DEFAULT_READER = Reader()

read = DEFAULT_READER.read
