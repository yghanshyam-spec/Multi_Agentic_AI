"""
agents/router/workflows/nodes/activate_agents_node.py
=======================================================
Node: ``activate_agents_node``

Deterministic node — records the ordered list of agents to activate,
derived from routing_plan.agent_priority_order (or required_agents as
fallback).

No LLM call. No langfuse_client or prompt_manager.
"""
from __future__ import annotations
import time

from shared.common import make_audit_event, build_trace_entry
from shared.state import RouterAgentState


def activate_agents_node(state: RouterAgentState) -> dict:
    """Deterministic node — records activated agents in routing priority order."""
    t0    = time.monotonic()
    order = (
        state.get("routing_plan", {}).get("agent_priority_order")
        or state.get("required_agents", [])
    )
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "activated_agents": order,
        "current_node":     "activate_agents_node",
        "execution_trace":  [build_trace_entry("activate_agents_node", duration_ms)],
        "audit_events":     [make_audit_event(
            state, "activate_agents_node", f"ACTIVATED:{order}"
        )],
    }
