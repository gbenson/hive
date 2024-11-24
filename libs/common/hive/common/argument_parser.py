import logging

from argparse import ArgumentParser

from .logging import getenv_log_level

logger = logging.getLogger(__name__)


class HiveArgumentParser(ArgumentParser):
    DEFAULT_EPILOG = "Run with LL=debug for so much extra logging."
    DEFAULT_LOGLEVEL = logging.INFO

    def parse_args(self, *args, **kwargs):
        if not self.epilog:
            self.epilog = self.DEFAULT_EPILOG

        if (log_level := getenv_log_level(default=self.DEFAULT_LOGLEVEL)):
            try:
                logging.basicConfig(level=log_level)
            except ValueError:
                logger.warning(f"Ignoring LL={log_level!r}")
        return super().parse_args(*args, *kwargs)
