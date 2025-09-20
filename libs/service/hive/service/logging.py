import logging
import sys

from logging import Formatter, StreamHandler

from pythonjsonlogger.json import JsonFormatter as JSONFormatter


def maybe_enable_json_logging() -> None:
    """Enable JSON logging if things look default and we don't have a tty.
    """
    if sys.stderr.isatty():
        return

    handlers = logging.root.handlers
    if len(handlers) != 1:
        return
    handler = handlers[0]
    if not isinstance(handler, StreamHandler):
        return
    if handler.stream != sys.stderr:
        return
    formatter = handler.formatter
    if not isinstance(formatter, Formatter):
        return

    # Probe the formatter to ensure it's nothing special.
    record = type("MockRecord", (), {})()
    record.__dict__.update((k, k) for k in ("levelname", "message", "name"))
    try:
        got = formatter.formatMessage(record)
    except Exception:
        return  # A field we didn't supply?  Whatever, it's not default...
    if got != "levelname:name:message":
        return  # Not default

    # Switch to stdout so Docker × journald records our messages
    # as PRIORITY=6 ("info") rather than PRIORITY=3 ("error").
    handler.setStream(sys.stdout)

    # Switch to JSON formatting.
    handler.setFormatter(JSONFormatter(
        "{name}{lineno}{levelname}{process}{thread}{threadName}{message}",
        style="{",
        rename_fields={
            "name": "logger",
            "levelname": "level",
            "process": "pid",
            "thread": "thread_id",
            "threadName": "thread_name",
        },
        defaults={
            "net_gbenson_logger": "hive-service-py",
        },
    ))
