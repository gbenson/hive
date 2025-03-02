import inspect
import os


def read_resource(filename: str, mode: str = "r") -> str | bytes:
    if not os.path.isabs(filename):
        if not (current_frame := inspect.currentframe()):
            raise NotImplementedError  # pragma: no cover
        if not (caller_frame := current_frame.f_back):
            raise NotImplementedError  # pragma: no cover
        caller_filename = caller_frame.f_code.co_filename
        filename = os.path.join(os.path.dirname(caller_filename), filename)
    with open(filename, mode) as fp:
        result: str | bytes = fp.read()
        return result
