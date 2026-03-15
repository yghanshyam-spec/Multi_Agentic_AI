# """
# utils/decorators.py
# ===================
# Reusable decorators: retry, timing, etc.
# """

# from __future__ import annotations

# import functools
# import time
# from typing import Callable, Any

# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# from agent_hitl.utils.logger import get_logger

# logger = get_logger(__name__)


# def timed(func: Callable) -> Callable:
#     """Log the wall-clock time of any function call."""
#     @functools.wraps(func)
#     def wrapper(*args: Any, **kwargs: Any) -> Any:
#         start = time.perf_counter()
#         result = func(*args, **kwargs)
#         elapsed = time.perf_counter() - start
#         logger.debug("Function timed", fn=func.__name__, seconds=round(elapsed, 3))
#         return result
#     return wrapper


# def with_retry(
#     attempts: int = 3,
#     wait_min: float = 1.0,
#     wait_max: float = 10.0,
#     exceptions: tuple = (Exception,),
# ) -> Callable:
#     """Decorator factory for exponential-backoff retries via tenacity."""
#     def decorator(func: Callable) -> Callable:
#         return retry(
#             stop=stop_after_attempt(attempts),
#             wait=wait_exponential(min=wait_min, max=wait_max),
#             retry=retry_if_exception_type(exceptions),
#             reraise=True,
#         )(func)
#     return decorator
