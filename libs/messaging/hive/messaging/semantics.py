import inspect
import logging

from typing import Any

from pika import DeliveryMode

logger = logging.getLogger(__name__)


def publish_may_drop(kwargs: dict[str, Any]):
    """Unroutable messages are silently dropped.
    """
    _ensure_kwarg(kwargs, "mandatory", False)


def publish_must_succeed(kwargs: dict[str, Any]):
    """The message is delivered or an exception is raised.
    """
    _ensure_kwarg(kwargs, "mandatory", True)
    messages_persist_across_broker_restarts(kwargs)


def messages_persist_across_broker_restarts(kwargs: dict[str, Any]):
    """The message won't get lost if the broker is restarted (part 1 of 2).
    """
    _ensure_kwarg(kwargs, "delivery_mode", DeliveryMode.Persistent)


_Unset = object()


def _ensure_kwarg(kwargs: dict[str, Any], name: str, required_value: Any):
    got_value = kwargs.get(name, _Unset)
    if got_value is _Unset:
        kwargs[name] = required_value
        return

    frame = inspect.currentframe()
    while frame and frame.f_code.co_filename == __file__:
        frame = frame.f_back
    func_name = frame.f_code.co_name

    if got_value is not required_value:
        raise ValueError(f"{func_name}:{name}={got_value!r}")

    logger.warning('%s: "%s" keyword argument is deprecated',
                   func_name, name, stacklevel=2)
