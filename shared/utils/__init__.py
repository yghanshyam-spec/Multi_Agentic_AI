"""
shared/utils/__init__.py
=========================
Utility package — exposes all utilities under shared.utils namespace.

  from shared.utils import build_trace_entry, safe_get   # core utils
  from shared.utils.logger import get_logger             # structured logger
  from shared.utils.helpers import truncate_text         # string helpers
  from shared.utils.decorators import retry              # decorators
"""
from shared._core_utils import build_trace_entry, truncate_history, safe_get, timed_node

__all__ = ["build_trace_entry", "truncate_history", "safe_get", "timed_node"]
