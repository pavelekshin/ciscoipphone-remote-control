import functools
import time


def async_timed():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            print(f"Run {func} with {args} and {kwargs}")
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"{func} ended on {total:.4f} sec")

        return wrapped

    return wrapper
