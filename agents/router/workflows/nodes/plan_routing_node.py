"""
agents/router/workflows/nodes/plan_routing_node.py
====================================================
Node function: ``plan_routing_node``

Single-responsibility node — part of the router LangGraph workflow.
"""
from __future__ import annotations
import os
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


def plan_routing_node(state: RouterAgentState) -> dict:
    """
    LLM node: determines execution_mode, agent_priority_order, fallback_agents.
    Prompt sourced from: Langfuse registry → consumer config → built-in default.
    """
    t0 = time.monotonic()
    sys_prompt  = _get_prompt("plan_routing", state)
    user_prompt = (
        f"Required agents: {state.get('required_agents', [])}\n"
        f"Load metrics: {state.get('load_metrics', {})}"
    )
    llm    = get_llm()
    result = call_llm(llm, sys_prompt, user_prompt, node_hint="plan_routing")
    log_llm_call("router_agent", "plan_routing_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
                 sys_prompt[:200], str(result), session_id=state.get("session_id", ""))
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "routing_plan":    result,
        "current_node":    "plan_routing_node",
        "execution_trace": [build_trace_entry("plan_routing_node", duration_ms, 180)],
    }
