import json
import logging
import subprocess

from pathlib import Path
from shutil import which

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)

    if not which("rsync"):
        logger.info("Installing rsync")
        subprocess.check_call(("apk", "add", "rsync"))

    SOURCE = Path("/etc/letsencrypt")
    TARGET = Path("/var/lib/hive/certdist")

    config = json.loads((TARGET / "config.json").read_text())
    for target, domains in config.items():
        target = TARGET / target
        logger.info("Updating %s", target)
        for domain in domains:
            try:
                sync(SOURCE, domain, target)
            except Exception:
                logger.exception("EXCEPTION")


def sync(source: Path, domain: str, target: Path) -> None:
    _sync(source, domain, target, "archive")
    _sync(source, domain, target, "live")
    _sync(source, domain, target, "archive", allow_deletion=True)


def _sync(
        source: Path,
        domain: str,
        target: Path,
        subdir: str,
        allow_deletion: bool = False,
) -> None:
    source = source / subdir / domain
    target = target / subdir
    target.mkdir(mode=0o700, exist_ok=True)

    command = ["rsync", "-ai"]
    if allow_deletion:
        command.append("--delete")
    command.extend(map(str, (source, target)))

    logger.debug("%s", " ".join(command))
    try:
        subprocess.check_call(command)
    except Exception:
        logger.exception("EXCEPTION")


if __name__ == "__main__":
    main()
