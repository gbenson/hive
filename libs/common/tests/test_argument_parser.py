import logging
import sys

import pytest

from hive.common import ArgumentParser
from hive.common.testing import want_to_see


@pytest.fixture(autouse=True)
def clean_commandline(monkeypatch):
    monkeypatch.setattr(sys, "argv", sys.argv[:1])


def test_hive_default_log_level(monkeypatch):
    logging_basicconfig_calls = []

    def mock_bc(*args, **kwargs):
        nonlocal logging_basicconfig_calls
        logging_basicconfig_calls.append((args, kwargs))

    with monkeypatch.context() as mp:
        mp.setattr(logging, "basicConfig", mock_bc)
        mp.delenv("LL", raising=False)
        _ = ArgumentParser().parse_args()

    assert logging_basicconfig_calls == [((), {"level": logging.INFO})]


def test_library_default_log_level(monkeypatch):
    def mock_bc(*args, **kwargs):
        pytest.fail("logging.basicConfig() was called")

    with monkeypatch.context() as mp:
        mp.setattr(logging, "basicConfig", mock_bc)
        mp.delenv("LL", raising=False)
        parser = ArgumentParser()
        parser.DEFAULT_LOGLEVEL = None
        _ = parser.parse_args()


@pytest.mark.parametrize(
    ("user_level", "expect_level"),
    (("debug", logging.DEBUG),
     ("DEBUG", logging.DEBUG),
     ("10", logging.DEBUG),
     ("11", 11),
     ("WARNING", logging.WARNING),
     ("critical", logging.CRITICAL),
     ))
def test_getenv_log_level(user_level, expect_level, monkeypatch):
    loggers = []

    def logger_name(i):
        return f"{__name__}.test_getenv_log_level.{i}"

    def mock_bc(level):
        logger = logging.getLogger(logger_name(len(loggers)))
        logger.setLevel(level)
        loggers.append(logger)

    with monkeypatch.context() as mp:
        mp.setattr(logging, "basicConfig", mock_bc)
        mp.setenv("LL", user_level)
        _ = ArgumentParser().parse_args()

    assert len(loggers) == 1
    logger = loggers[0]
    assert logger.name == logger_name(0)
    assert logger.level == expect_level


def test_unknown_log_level(monkeypatch, caplog):
    def mock_bc(level):
        logger = logging.getLogger(f"{__name__}.test_unknown_log_level")
        logger.setLevel(level)
        pytest.fail(f"logger.setLevel({level!r}) didn't raise")

    with monkeypatch.context() as mp:
        mp.setattr(logging, "basicConfig", mock_bc)
        mp.setenv("LL", "gonk")

        with caplog.at_level(logging.WARNING):
            _ = ArgumentParser().parse_args()

    want_to_see(caplog, "Ignoring LL='GONK'")
