from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryFile
from typing import Any, Optional

from hishel import CacheClient, FileStorage
from httpx import Client, Request, Response, URL  # noqa: F401

from .config import read as read_config
from .xdg import user_cache_dir
from .__version__ import __version__

__url__ = "https://github.com/gbenson/hive"


def _default_cache_path_options() -> Iterator[Path]:
    if (path := user_cache_dir()):
        yield path
    for dirname in ("/var/cache", "/var/tmp", "/tmp"):
        yield Path(dirname)


def _special_mkdir(path: Path, mode: int = 0o700) -> Path:
    path = path.resolve()
    path.mkdir(mode=mode, parents=True, exist_ok=True)
    path.chmod(mode)
    with TemporaryFile(dir=path):
        pass
    return path


def _default_cache_path() -> Optional[Path]:
    for basedir in _default_cache_path_options():
        with suppress(PermissionError):
            return _special_mkdir(basedir / "hive" / "hishel")
    return None


DEFAULT_CACHE_PATH = _default_cache_path()


def _default_user_agent(name: str = "HiveBot") -> str:
    config_key = name.lower()
    try:
        template = read_config(config_key)[config_key]["user_agent"]
    except KeyError:
        template = f"{name}/{{version}} (bot; +{__url__})"
    return template.format(version=__version__)


DEFAULT_USER_AGENT = _default_user_agent()


DEFAULT_CLIENT: Client = CacheClient(
    http2=True,
    storage=FileStorage(base_path=DEFAULT_CACHE_PATH),
)
DEFAULT_CLIENT.headers["User-Agent"] = DEFAULT_USER_AGENT


globals().update(
    (attr, getattr(DEFAULT_CLIENT, attr))
    for attr in (
            "delete",
            "get",
            "head",
            "options",
            "patch",
            "post",
            "put",
            "request",
            "stream",
    )
)


def response_as_json(r: Response) -> dict[str, Any]:
    return {
        "url": str(r.url),
        "http_version": r.http_version,
        "status_code": r.status_code,
        "reason_phrase": r.reason_phrase,
        "headers": r.headers.multi_items(),
        "body": r.text,
    }
