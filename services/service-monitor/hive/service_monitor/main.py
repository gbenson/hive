import logging

from hive.common.functools import once
from hive.service import RestartMonitor

from .service import Service


def main():
    logging.basicConfig(level=logging.INFO)
    rsm = RestartMonitor()
    service = Service(
        service_condition_window=rsm.rapid_restart_cutoff,
        on_channel_open=once(rsm.report_via_channel),
    )
    service.run()
