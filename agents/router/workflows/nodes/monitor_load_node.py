"""
agents/router/workflows/nodes/monitor_load_node.py
====================================================
Node: ``monitor_load_node``

Deterministic node — queries LoadMonitor for per-agent health and queue
depth metrics that inform the routing decision.

No LLM call. No langfuse_client or prompt_manager.
"""
from __future__ import annotations
import time

from shared.common import (
    make_audit_event, build_trace_entry,
)
from shared.state import RouterAgentState
from agents.router.tools.load_monitor import LoadMonitor, AGENT_REGISTRY

_load_monitor = LoadMonitor()


def _agent_list(state: RouterAgentState) -> list:
    return state.get("config", {}).get("agent_registry", AGENT_REGISTRY)


def monitor_load_node(state: RouterAgentState) -> dict:
    """Deterministic node — queries LoadMonitor tool for per-agent health metrics."""
    t0          = time.monotonic()
    metrics     = _load_monitor.get_metrics(_agent_list(state))
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "load_metrics":    metrics,
        "current_node":    "monitor_load_node",
        "execution_trace": [build_trace_entry("monitor_load_node", duration_ms)],
    }
