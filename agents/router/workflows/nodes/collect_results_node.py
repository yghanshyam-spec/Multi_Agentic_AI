"""
agents/router/workflows/nodes/collect_results_node.py
=======================================================
Node function: ``collect_results_node``

Single-responsibility node — part of the router LangGraph workflow.
"""
from __future__ import annotations
import time, json, re, hashlib
from typing import Any, Optional

from shared.common import (
    get_llm, call_llm, get_prompt, log_llm_call, get_tracer,
    make_audit_event, build_trace_entry, make_base_state, new_id, utc_now,
    ExecutionStatus, build_agent_response, AgentType, safe_get, truncate_text,

    get_last_token_usage,
)
from agents.router.prompts.defaults import get_default_prompt
from agents.router.tools.load_monitor import LoadMonitor, AGENT_REGISTRY
# router_nodes circular import removed

# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
_load_monitor = LoadMonitor()

# ── Private helpers ────────────────────────────────────────────────────────────
def _agent_list(state: RouterAgentState) -> list:
    return state.get("config", {}).get("agent_registry", AGENT_REGISTRY)

def _get_prompt(key: str, state: RouterAgentState, **kwargs) -> str:
    consumer_override = state.get("config", {}).get("prompts", {}).get(key)
    fallback = consumer_override or get_default_prompt(f"router_{key}")
    return get_prompt(f"router_{key}", agent_name="router", fallback=fallback, **kwargs)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"router_{key}")
    return get_prompt(f"router_{key}", agent_name="router", fallback=fb, **kw)


def collect_results_node(state: RouterAgentState) -> dict:
    """Deterministic: gathers partial_results from all activated agents."""
    t0 = time.monotonic()
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "current_node":    "collect_results_node",
        "execution_trace": [build_trace_entry("collect_results_node", duration_ms)],
    }
