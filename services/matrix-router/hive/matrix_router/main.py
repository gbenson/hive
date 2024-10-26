import logging

from hive.common.functools import once
from hive.service import RestartMonitor

from .router import Router
from .service import Service


class RouterService(Router, Service):
    pass


def main():
    logging.basicConfig(level=logging.INFO)
    rsm = RestartMonitor()
    service = RouterService(on_channel_open=once(rsm.report_via_channel))
    service.run()
