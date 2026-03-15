"""
shared/utils/decorators.py
===========================
Production-grade decorators shared across all agents.

    @retry(max_attempts=3, exceptions=(Exception,), delay=0.5)
    def my_llm_call(): ...

    @log_call(logger)
    def my_node(state): ...

    @with_timeout(seconds=30)
    async def my_async_node(state): ...
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, Tuple, Type


def retry(
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    delay: float = 0.5,
    backoff: float = 2.0,
    logger=None,
) -> Callable:
    """
    Retry decorator with exponential back-off.

    Parameters
    ----------
    max_attempts : total attempts (including the first)
    exceptions   : tuple of exception types to catch and retry
    delay        : initial sleep between retries (seconds)
    backoff      : multiplier applied to delay after each retry
    logger       : optional logger (uses print as fallback)
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        msg = (
                            f"[retry] {fn.__qualname__} attempt {attempt}/{max_attempts} "
                            f"failed: {exc}. Retrying in {current_delay:.1f}s…"
                        )
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


def log_call(logger=None, level: str = "debug") -> Callable:
    """
    Log entry/exit of a function at the specified level.
    Useful for wrapping node functions during debugging.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            log_fn = getattr(logger, level, print) if logger else print
            log_fn(f"→ {fn.__qualname__}")
            t0 = time.monotonic()
            try:
                result = fn(*args, **kwargs)
                elapsed = int((time.monotonic() - t0) * 1000)
                log_fn(f"← {fn.__qualname__} ({elapsed}ms)")
                return result
            except Exception as exc:
                elapsed = int((time.monotonic() - t0) * 1000)
                err_fn = getattr(logger, "error", print) if logger else print
                err_fn(f"✗ {fn.__qualname__} ({elapsed}ms) — {exc}")
                raise
        return wrapper
    return decorator


def with_timeout(seconds: float) -> Callable:
    """
    Raise TimeoutError if an async coroutine exceeds *seconds*.
    (No-op for sync functions — use threading.Timer for sync timeouts.)
    """
    def decorator(fn: Callable) -> Callable:
        import asyncio

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs) -> Any:
            return await asyncio.wait_for(fn(*args, **kwargs), timeout=seconds)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs) -> Any:
            # For sync functions just call directly; true timeout requires threads
            return fn(*args, **kwargs)

        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    return decorator
