"""
agents/router/workflows/nodes/analyse_request_node.py
=======================================================
Node function: ``analyse_request_node``

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
# _agent_list defined locally below

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


def analyse_request_node(state: RouterAgentState) -> dict:
    """
    LLM node: determines which agents are needed, priority, complexity.
    Prompt sourced from: Langfuse registry → consumer config → built-in default.
    """
    t0 = time.monotonic()
    tracer = get_tracer("router_agent")
    agents = ", ".join(_agent_list(state))

    sys_prompt  = _get_prompt("analyse_request", state, agents=agents)
    user_prompt = f"User request: {state['raw_input']}"

    llm    = get_llm()
    result = call_llm(llm, sys_prompt, user_prompt, node_hint="analyse_request")
    log_llm_call("router_agent", "analyse_request_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
                 sys_prompt[:200], str(result), session_id=state.get("session_id", ""))

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "required_agents":  result.get("required_agents", ["INTENT_AGENT"]),
        "parallel_safe":    result.get("parallel_safe", False),
        "priority":         result.get("priority", "medium"),
        "status":           ExecutionStatus.RUNNING,
        "current_node":     "analyse_request_node",
        "execution_trace":  [build_trace_entry("analyse_request_node", duration_ms, 250)],
        "audit_events":     [make_audit_event(state, "analyse_request_node", "REQUEST_ANALYSED")],
    }
