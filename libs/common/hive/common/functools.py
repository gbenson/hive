from itertools import count
from typing import Callable, Optional


def once(func):
    """Decorator that ensures func runs only once.
    """
    counter = count()
    def wrapper(*args, **kwargs):
        if next(counter) != 0:
            return None
        return func(*args, **kwargs)
    return wrapper


def chained(*funcs) -> Optional[Callable]:
    """Return a callable that's equivalent to calling each not-None
    supplied callable in sequence with the same arguments.  If all
    supplied callables are None then None is returned.
    """
    funcs = [func for func in funcs if func]
    if not funcs:
        return None
    if len(funcs) == 1:
        return funcs[0]

    def result(*args, **kwargs):
        for func in funcs:
            func(*args, **kwargs)

    return result
