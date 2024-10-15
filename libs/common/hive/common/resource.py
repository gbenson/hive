import inspect
import os


def read_resource(filename: str, mode: str = "r") -> str | bytes:
    if not os.path.isabs(filename):
        caller_filename = inspect.currentframe().f_back.f_code.co_filename
        filename = os.path.join(os.path.dirname(caller_filename), filename)
    with open(filename, mode) as fp:
        return fp.read()
