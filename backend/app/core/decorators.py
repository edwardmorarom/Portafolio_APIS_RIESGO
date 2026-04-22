from __future__ import annotations

import functools
import logging
import time

logger = logging.getLogger("portafolio_riesgo")


def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("%s executed in %.4f seconds", func.__name__, elapsed)
        return result

    return wrapper