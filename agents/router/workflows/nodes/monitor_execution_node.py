"""
agents/router/workflows/nodes/monitor_execution_node.py
=========================================================
Node: ``monitor_execution_node``

Deterministic node — checks for stalls or timeouts across active agents
after activation. In the current implementation this is a lightweight
passthrough that can be extended with real health-check logic.

No LLM call. No langfuse_client or prompt_manager.
"""
from __future__ import annotations
import time

from shared.common import make_audit_event, build_trace_entry
from shared.state import RouterAgentState


def monitor_execution_node(state: RouterAgentState) -> dict:
    """Deterministic node — monitors active agent execution for stalls/timeouts."""
    t0          = time.monotonic()
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "current_node":    "monitor_execution_node",
        "execution_trace": [build_trace_entry("monitor_execution_node", duration_ms)],
    }
