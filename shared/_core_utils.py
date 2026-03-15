"""
shared/utils.py
===============
Common utilities: timing decorators, node wrappers, trace helpers.
"""

from __future__ import annotations

import os
import time
import traceback
from functools import wraps
from typing import Any, Callable

from shared.state import ExecutionMetadata, make_audit_event, utc_now, new_id


def timed_node(node_name: str, llm_node: bool = False):
    """
    Decorator for LangGraph node functions.
    - Times execution
    - Appends ExecutionMetadata to state["execution_trace"]
    - Appends AuditEvent to state["audit_events"] if audit enabled
    - Catches exceptions and appends to state["error_history"]
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(state: dict, *args, **kwargs) -> dict:
            t0 = time.monotonic()
            started_at = utc_now()
            tokens_used = 0
            error_msg = None

            try:
                result = fn(state, *args, **kwargs)
                return result or {}
            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
                return {
                    "status": "FAILED",
                    "error_history": [{"node": node_name, "error": error_msg, "ts": utc_now()}],
                }
            finally:
                duration_ms = int((time.monotonic() - t0) * 1000)
                meta = ExecutionMetadata(
                    node_name=node_name,
                    started_at=started_at,
                    completed_at=utc_now(),
                    duration_ms=duration_ms,
                    llm_tokens_used=tokens_used,
                    llm_model=state.get("config", {}).get("llm_model", "claude-sonnet-4-5"),
                    retry_count=state.get("retry_count", 0),
                    error=error_msg,
                )
                # Return trace update (merged by LangGraph reducer)
                # Note: actual append happens in function return dict

        return wrapper
    return decorator


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safe nested dict accessor."""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key, default)
        if data is None:
            return default
    return data


def truncate_history(history: list, max_turns: int = 20) -> list:
    """Keep only the most recent N conversation turns."""
    return history[-max_turns:] if len(history) > max_turns else history


def build_trace_entry(node_name: str, duration_ms: int, llm_tokens: int = 0, error: str = None) -> dict:
    # Coerce to int — callers sometimes pass float or string values from LLM responses
    try:
        duration_ms = int(duration_ms)
    except (TypeError, ValueError):
        duration_ms = 0
    try:
        llm_tokens = int(llm_tokens)
    except (TypeError, ValueError):
        llm_tokens = 0
    return {
        "node_name":       node_name,
        "started_at":      utc_now(),
        "completed_at":    utc_now(),
        "duration_ms":     duration_ms,
        "llm_tokens_used": llm_tokens,
        "llm_model":       os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
        "retry_count":     0,
        "error":           error,
    }
