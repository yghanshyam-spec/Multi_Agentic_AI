"""
agents/router/workflows/nodes/plan_routing_node.py
====================================================
Node: ``plan_routing_node``

LLM node — given the required agents and live load metrics, determines the
optimal execution_mode (sequential / parallel / batched), agent_priority_order,
and fallback_agents.

Tracing & prompts: shared.langfuse_manager only (via shared.common).
No local langfuse_client or prompt_manager.
"""
from __future__ import annotations
import os
import time

from shared.common import (
    get_llm, call_llm, get_prompt, log_llm_call,
    make_audit_event, build_trace_entry, get_last_token_usage,
)
from shared.state import RouterAgentState
from agents.router.prompts.defaults import get_default_prompt
from agents.router.tools.load_monitor import AGENT_REGISTRY

_AGENT_NAME = "router"


def _p(key: str, state: RouterAgentState, **kwargs) -> str:
    """Resolve prompt: shared.langfuse_manager registry → consumer config → built-in default."""
    fallback = (
        state.get("config", {}).get("prompts", {}).get(key)
        or get_default_prompt(f"router_{key}")
    )
    return get_prompt(f"router_{key}", agent_name=_AGENT_NAME, fallback=fallback, **kwargs)


def plan_routing_node(state: RouterAgentState) -> dict:
    """
    LLM node — determines execution_mode, agent_priority_order, fallback_agents.

    Prompt resolution: Langfuse registry → consumer config override → built-in default.
    """
    t0          = time.monotonic()
    sys_prompt  = _p("plan_routing", state)
    user_prompt = (
        f"Required agents: {state.get('required_agents', [])}\n"
        f"Load metrics: {state.get('load_metrics', {})}"
    )

    llm    = get_llm()
    result = call_llm(llm, sys_prompt, user_prompt, node_hint="plan_routing")
    log_llm_call(
        "router_agent", "plan_routing_node",
        os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
        sys_prompt[:200], str(result),
        session_id=state.get("session_id", ""),
        token_usage=get_last_token_usage(),
    )

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "routing_plan":    result,
        "current_node":    "plan_routing_node",
        "execution_trace": [build_trace_entry("plan_routing_node", duration_ms, 180)],
        "audit_events":    [make_audit_event(state, "plan_routing_node", "ROUTING_PLANNED")],
    }
