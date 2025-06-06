import copy
import logging
import re

from collections import defaultdict
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from certbot import crypto_util
from certbot._internal import cli, storage
from certbot._internal.plugins import disco as plugins_disco
from certbot._internal.renewal import reconstitute
from certbot._internal.storage import ALL_FOUR

logger = logging.getLogger(__name__)

FILENAME_RX = re.compile(rf"(?:{'|'.join(ALL_FOUR)})([0-9]+)\.pem")


def main():
    logging.basicConfig(level=logging.INFO)

    expired_files = list(certbot_expired_files())
    if not expired_files:
        logger.info("No expired files found")
        return

    for path in expired_files:
        logger.info("%s: Deleting", path)
        try:
            path.unlink()
        except Exception:
            logger.exception("EXCEPTION")
            continue


def certbot_expired_files() -> Iterable[Path]:
    # certbot/_internal/main.py: main
    plugins = plugins_disco.PluginsRegistry.find_all()
    config = cli.prepare_and_parse_args(plugins, [])

    # certbot/_internal/renewal.py: handle_renewal_request
    conf_files = storage.renewal_conf_files(config)
    for renewal_file in conf_files:
        # reconstitute updates config with elements from
        # the renewal file, so we need to work on a copy.
        lineage_config = copy.deepcopy(config)

        try:
            lineage = reconstitute(lineage_config, renewal_file)
        except Exception:
            logger.exception("EXCEPTION")
            continue

        if not lineage:
            logger.error("reconstitute(%r) returned %r", renewal_file, lineage)
            continue

        try:
            for expired_file in lineage_expired_files(lineage):
                yield expired_file
        except Exception:
            logger.exception("EXCEPTION")
            continue


def lineage_expired_files(lineage: storage.RenewableCert) -> Iterator[Path]:
    archive_dir = Path(lineage.archive_dir)

    paths_by_version = defaultdict(set)
    for path in archive_dir.iterdir():
        match = FILENAME_RX.fullmatch(path.name)
        if not match:
            logger.warning("%s: Unexpected file", path)
            continue
        paths_by_version[int(match.group(1))].add(path)

    for version, paths in sorted(paths_by_version.items()):
        cert_path = lineage.version("cert", version)
        if Path(cert_path) not in paths:
            logger.warning("%s: File not found", cert_path)
            continue
        # certbot/_internal/storage.py: RenewableCert.target_expiry
        expiry = crypto_util.notAfter(cert_path)
        if datetime.now(tz=timezone.utc) < expiry:
            continue  # not expired
        logger.info("%s: Certificate is expired", cert_path)
        for path in sorted(paths):
            yield path


if __name__ == "__main__":
    main()
