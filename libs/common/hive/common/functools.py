from itertools import count


def once(func):
    """Decorator that ensures func runs only once.
    """
    counter = count()
    def wrapper(*args, **kwargs):
        if next(counter) != 0:
            return None
        return func(*args, **kwargs)
    return wrapper
