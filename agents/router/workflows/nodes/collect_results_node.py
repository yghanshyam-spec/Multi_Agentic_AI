"""
agents/router/workflows/nodes/collect_results_node.py
=======================================================
Node: ``collect_results_node``

Deterministic node — gathers partial_results from all activated agents
into state for consumption by orchestrate_response_node.

No LLM call. No langfuse_client or prompt_manager.
"""
from __future__ import annotations
import time

from shared.common import make_audit_event, build_trace_entry
from shared.state import RouterAgentState


def collect_results_node(state: RouterAgentState) -> dict:
    """Deterministic node — collects and aggregates partial agent results."""
    t0          = time.monotonic()
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "current_node":    "collect_results_node",
        "execution_trace": [build_trace_entry("collect_results_node", duration_ms)],
        "audit_events":    [make_audit_event(
            state, "collect_results_node",
            f"RESULTS_COLLECTED:count={len(state.get('partial_results', []))}"
        )],
    }
