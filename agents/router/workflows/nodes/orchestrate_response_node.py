"""
agents/router/workflows/nodes/orchestrate_response_node.py
============================================================
Node function: ``orchestrate_response_node``

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


def orchestrate_response_node(state: RouterAgentState) -> dict:
    """
    LLM node: synthesises all agent results into a single coherent response.
    Prompt sourced from: Langfuse registry → consumer config → built-in default.
    """
    t0 = time.monotonic()
    partial = state.get("partial_results", [])
    sys_prompt  = _get_prompt("orchestrate_response", state)
    user_prompt = (
        f"Original request: {state['raw_input']}\n"
        f"Agent results: {partial}"
    )
    llm    = get_llm()
    result = call_llm(llm, sys_prompt, user_prompt, node_hint="orchestrate_response")
    log_llm_call("router_agent", "orchestrate_response_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
                 sys_prompt[:200], str(result), session_id=state.get("session_id", ""))

    summary = result.get("summary", "All agents completed their assigned tasks successfully.")
    duration_ms = int((time.monotonic() - t0) * 1000)

    response = build_agent_response(
        state,
        payload={
            "summary":          summary,
            "key_findings":     result.get("key_findings", []),
            "agents_activated": state.get("activated_agents", []),
            "routing_plan":     state.get("routing_plan", {}),
        },
        confidence_score=0.92,
    )
    return {
        "final_response":  summary,
        "agent_response":  dict(response),
        "status":          ExecutionStatus.COMPLETED,
        "current_node":    "orchestrate_response_node",
        "execution_trace": [build_trace_entry("orchestrate_response_node", duration_ms, 300)],
        "audit_events":    [make_audit_event(state, "orchestrate_response_node",
                            "ORCHESTRATION_COMPLETE")],
    }
