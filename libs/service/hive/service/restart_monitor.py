import logging
import os
import time

from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import Optional

from hive.common.units import MINUTES
from hive.messaging import Channel

from .status import ServiceCondition, ServiceStatus

logger = logging.getLogger(__name__)


@dataclass
class RestartMonitor:
    basename: str = ".hive-service-restart.stamp"
    dirname: str = field(default_factory=os.getcwd)
    status: ServiceStatus = field(default_factory=ServiceStatus)
    rapid_restart_cutoff: float = 5 * MINUTES
    rapid_restart_cooldown_time: Optional[float] = None
    multiple_restarts_logged: bool = False

    @property
    def name(self):
        return self.status.service

    @property
    def stamp_filename(self) -> str:
        return os.path.join(self.dirname, self.basename)

    @stamp_filename.setter
    def stamp_filename(self, value: str):
        self.dirname, self.basename = os.path.split(value)

    @property
    def stamp_filenames(self) -> tuple[str, str, str]:
        main_filename = self.stamp_filename
        base, ext = os.path.splitext(main_filename)
        result = tuple(
            f"{base}{midfix}{ext}"
            for midfix in (".n-2", ".n-1", "", ".n+1")
        )
        return result

    def __post_init__(self):
        try:
            self._run()
        except Exception:
            self.log_exception()
        logger.info("Service status: %s", self.status.condition.name)

    def log(self, message, level=logging.INFO):
        if self.status.condition is not ServiceCondition.IN_ERROR:
            if level > logging.WARNING:
                self.status.condition = ServiceCondition.IN_ERROR
            elif level > logging.INFO:
                self.status.condition = ServiceCondition.DUBIOUS
        message = f"Service {message}"
        logger.log(level, message)
        self.status.messages.append(message)

    def warn_rapid_restart(self, interval: float, level=logging.WARNING):
        self.log(f"restarted after only {interval:.3f} seconds", level=level)

    def log_rapid_cycling(self, interval: float):
        self.warn_rapid_restart(interval, level=logging.ERROR)
        self.log("is restarting rapidly", level=logging.ERROR)

    def log_exception(self):
        self.status.condition = ServiceCondition.IN_ERROR
        logger.exception("EXCEPTION")

    def _run(self):
        filenames = self.stamp_filenames
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
        self.status.timestamp = datetime.fromtimestamp(
            this_startup, timezone.utc)

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

        self.multiple_restarts_logged = True

    def _cool_your_engines(self):
        """https://www.youtube.com/watch?v=rsHqcUn6jBY
        """
        cooldown_time = self.rapid_restart_cooldown_time
        if cooldown_time is None:
            cooldown_time = self.rapid_restart_cutoff // 3
        logger.info(f"Sleeping for {cooldown_time} seconds")
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

    def report_via_channel(self, channel: Channel, **kwargs):
        """Report this startup via a :class:`hive.messaging.Channel`.
        """
        return self.status.report_via_channel(channel, **kwargs)
