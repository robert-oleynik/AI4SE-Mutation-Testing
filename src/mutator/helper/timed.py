from functools import wraps
from time import time


def timed(f):
    @wraps(f)
    def wrap(*args, **kw):
        start = time()
        result = f(*args, **kw)
        end = time()
        duration = end - start
        print(f"{f.__name__} took {duration:2.4f} seconds")
        return result

    return wrap
