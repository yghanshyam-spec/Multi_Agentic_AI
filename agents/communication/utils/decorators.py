"""
communication/utils/decorators.py
Retry, timing, and circuit-breaker decorators.
"""
from __future__ import annotations

import functools
import time
from typing import Callable, Tuple, Type

from utils.logger import get_logger

logger = get_logger(__name__)


def retry(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            delay = wait_seconds
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    logger.warning(
                        f"[RETRY] {fn.__name__} attempt {attempt}/{max_attempts}: {exc}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator


def timed(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        logger.debug(f"[TIMED] {fn.__name__} completed in {time.perf_counter()-t0:.3f}s")
        return result
    return wrapper
