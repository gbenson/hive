import os
import logging
import random
import subprocess
import sys

from datetime import datetime, time, timedelta
from time import sleep

logger = logging.getLogger(__name__)

WINDOW_START = time(hour=4)
WINDOW_LIMIT = time(hour=5)


def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        _main_loop()


def _main_loop():
    sleep_until_next_window()
    run_system("certbot", "renew")
    run_python("delete_expired.py")
    run_python("update_certdist_roots.py")


def sleep_until_next_window():
    # This will be an hour out on zone change days.
    now = datetime.now()
    window_start = datetime.combine(now.date(), WINDOW_START)
    if window_start < now:
        window_start += timedelta(days=1)
    logger.info("Next window opens at %s", window_start)
    window_limit = datetime.combine(window_start.date(), WINDOW_LIMIT)
    window_seconds = (window_limit - window_start).total_seconds()
    jitter = random.randrange(1, round(window_seconds))
    # (never zero jitter so we always wake in the window)
    wakeup_time = window_start + timedelta(seconds=jitter)
    logger.info("Sleeping until %s", wakeup_time)
    sleep((wakeup_time - now).total_seconds())


def run_system(*command):
    try:
        subprocess.check_call(command)
    except Exception:
        logger.exception("EXCEPTION")


def run_python(filename, *args):
    filename = os.path.join(os.path.dirname(__file__), filename)
    run_system(sys.executable, filename, *args)


if __name__ == "__main__":
    main()
