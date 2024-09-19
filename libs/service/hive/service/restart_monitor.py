import logging
import os
import sys
import time

from collections.abc import Iterator
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

ServiceStatus = Enum("ServiceStatus", "HEALTHY DUBIOUS IN_ERROR")

MINUTES = 60


@dataclass
class RestartMonitor:
    try:
        DEFAULT_NAME = os.path.basename(sys.argv[0])
        DEFAULT_INITIAL_STATUS = ServiceStatus.HEALTHY
    except Exception as e:
        DEFAULT_NAME = f"[ERROR: {e}]"
        DEFAULT_INITIAL_STATUS = ServiceStatus.DUBIOUS

    name: str = DEFAULT_NAME
    basename: str = ".hive-service-restart.stamp"
    dirname: str = field(default_factory=os.getcwd)
    status: ServiceStatus = DEFAULT_INITIAL_STATUS
    rapid_restart_cutoff: float = 5 * MINUTES
    rapid_restart_cooldown_time: Optional[float] = None

    @property
    def filename(self) -> str:
        return os.path.join(self.dirname, self.basename)

    @filename.setter
    def filename(self, value: str):
        self.dirname, self.basename = os.path.split(value)

    @property
    def filenames(self) -> tuple[str, str, str]:
        main_filename = self.filename
        base, ext = os.path.splitext(main_filename)
        result = tuple(
            f"{base}{midfix}{ext}"
            for midfix in (".n-2", ".n-1", "", ".n+1")
        )
        return result

    def __post_init__(self):
        self._messages = []
        try:
            self._run()
        except Exception:
            self.status = ServiceStatus.IN_ERROR
            self.log_exception()

    def log(self, message, level=logging.INFO):
        if self.status is not ServiceStatus.IN_ERROR:
            if level > logging.WARNING:
                self.status = ServiceStatus.IN_ERROR
            elif level > logging.INFO:
                self.status = ServiceStatus.DUBIOUS
        logger.log(level, message)
        self._messages.append(message)

    def warn(self, message):
        self.log(message, level=logging.WARNING)

    def log_error(self, message):
        self.log(message, level=logging.ERROR)

    def warn_rapid_restart(self, interval: float):
        self.warn(f"restarted after only {interval:.3f} seconds")

    def log_rapid_cycling(self, interval: float):
        self.warn_rapid_restart(interval)
        self.log_error("is restarting rapidly")

    def log_exception(self):
        self.status = ServiceStatus.IN_ERROR
        logger.exception("LOGGED EXCEPTION")

    @property
    def messages(self) -> Iterator[tuple[int, str]]:
        return (f"{self.name} {msg}" for msg in self._messages)

    def _run(self):
        filenames = self.filenames
        self.touch(filenames[-1])
        timestamps = tuple(map(self.getmtime, filenames))
        self._handle_situation(*timestamps)
        self._rotate(filenames)

    def _handle_situation(
            self,
            startup_two_before_last: Optional[float],
            startup_before_last: Optional[float],
            last_startup: Optional[float],
            this_startup: float,
    ):
        if last_startup is None:
            self.log("started for the first time")
            return

        this_interval = this_startup - last_startup
        if this_interval > self.rapid_restart_cutoff:
            self.log("restarted")
            return

        # at least one rapid restart

        if startup_before_last is None:
            self.warn_rapid_restart(this_interval)
            return

        last_interval = last_startup - startup_before_last
        if last_interval > self.rapid_restart_cutoff:
            self.warn_rapid_restart(this_interval)
            return

        # at least two rapid restarts in succession

        self.log_rapid_cycling(this_interval)
        self._cool_your_engines()

        if startup_two_before_last is None:
            return

        last_last_interval = startup_before_last - startup_two_before_last
        if last_last_interval > self.rapid_restart_cutoff:
            return

        # at least three rapid restarts in succession

        self._messages = []  # DO NOT LOG!

    def _cool_your_engines(self):
        """https://www.youtube.com/watch?v=rsHqcUn6jBY
        """
        cooldown_time = self.rapid_restart_cooldown_time
        if cooldown_time is None:
            cooldown_time = self.rapid_restart_cutoff // 3
        logger.info(f"sleeping for {cooldown_time} seconds")
        time.sleep(cooldown_time)

    def _rotate(self, filenames):
        for dst, src in zip(filenames[:-1], filenames[1:]):
            try:
                if os.path.exists(src):
                    os.rename(src, dst)
            except Exception:
                self.log_exception()

    @staticmethod
    def getmtime(filename: str) -> Optional[float]:
        """Return a file's last modification time, or None if not found.
        """
        try:
            return os.path.getmtime(filename)
        except OSError:
            return None

    @staticmethod
    def touch(filename: str):
        """Set a file's access and modified times to the current time.
        """
        try:
            os.utime(filename)
        except FileNotFoundError:
            open(filename, "wb").close()
