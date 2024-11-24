import logging
import os

from collections.abc import Iterable
from importlib import import_module, reload
from pkgutil import iter_modules

from . import handlers
from .handler import Handler

logger = logging.getLogger(__name__)


class HandlerLoader:
    def __init__(self, toplevel_module=handlers, handler_type=Handler):
        self.toplevel_module = toplevel_module
        self.handler_type = handler_type
        self._handlers = {}

    @property
    def package_name(self) -> str:
        return self.toplevel_module.__package__

    @property
    def search_path(self) -> list[str]:
        return self.toplevel_module.__path__

    @property
    def module_names(self) -> Iterable[str]:
        package_name = self.package_name
        for module_info in iter_modules(self.search_path):
            if not module_info.ispkg:
                yield f"{package_name}.{module_info.name}"

    @property
    def modules(self):
        for name in self.module_names:
            try:
                module = import_module(name)
                m_mtime = getattr(module, "__mtime__", None)
                f_mtime = os.path.getmtime(module.__file__)
                if f_mtime != m_mtime:
                    stale_handlers = [
                        key
                        for key, handler in self._handlers.items()
                        if handler.__class__.__module__ == name
                    ]
                    for handler in sorted(stale_handlers):
                        logger.info("Unlinking %s", handler)
                        self._handlers.pop(handler)

                    if m_mtime:
                        logger.info("Reloading %s", name)
                        reload(module)
                    else:
                        logger.info("Loaded %s", name)
                    module.__mtime__ = f_mtime
                yield module
            except Exception:
                logger.exception("EXCEPTION")

    @property
    def handler_classes(self):
        for module in self.modules:
            for attr in dir(module):
                if attr.startswith("_"):
                    continue
                item = getattr(module, attr)
                if item is self.handler_type:
                    continue
                try:
                    if issubclass(item, self.handler_type):
                        yield item
                except TypeError:
                    pass

    @property
    def handlers(self) -> Iterable[Handler]:
        for cls in self.handler_classes:
            fullname = f"{cls.__module__}.{cls.__name__}"
            handler = self._handlers.get(fullname)
            try:
                if isinstance(handler, cls):
                    yield handler
                    continue

                logger.info(
                    "%s %s",
                    ("Recreating" if handler else "Creating"),
                    fullname,
                )
                self._handlers[fullname] = handler = cls()
                yield handler

            except Exception:
                logger.exception("EXCEPTION")

    def __iter__(self):
        return (
            handler
            for _, handler in sorted(
                    ((handler.priority,
                      handler.__class__.__module__,
                      handler.__class__.__name__,
                      id(handler)),
                     handler)
                    for handler in self.handlers
            )
        )
