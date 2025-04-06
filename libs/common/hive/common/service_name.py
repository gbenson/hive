import os
import sys


def service_name() -> str:
    service_name = sys.argv[0]
    if service_name != "-m":
        return os.path.basename(service_name)
    for a, b in zip(sys.orig_argv[:-1], sys.orig_argv[1:]):
        if a != "-m":
            continue
        c, _, d = b.partition(".")
        if c != "hive":
            continue
        return "hive-" + d.replace("_", "-")
    raise NotImplementedError


try:
    SERVICE_NAME = service_name().removeprefix("hive-")
except Exception:
    SERVICE_NAME = "unknown-service"
