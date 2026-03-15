"""
agents/router/workflows/nodes/analyse_request_node.py
=======================================================
Node: ``analyse_request_node``

LLM node — determines which agents are needed, execution priority, and
request complexity.

Tracing & prompts: shared.langfuse_manager only (via shared.common).
No local langfuse_client or prompt_manager.
"""
from __future__ import annotations
import os
import time

from shared.common import (
    get_llm, call_llm, get_prompt, log_llm_call, get_tracer,
    make_audit_event, build_trace_entry,
    ExecutionStatus, get_last_token_usage,
)
from shared.state import RouterAgentState
from agents.router.prompts.defaults import get_default_prompt
from agents.router.tools.load_monitor import LoadMonitor, AGENT_REGISTRY

_load_monitor = LoadMonitor()


def _agent_list(state: RouterAgentState) -> list:
    return state.get("config", {}).get("agent_registry", AGENT_REGISTRY)


def _p(key: str, state: RouterAgentState, **kwargs) -> str:
    """Resolve prompt: shared.langfuse_manager registry → consumer config → built-in default."""
    fallback = (
        state.get("config", {}).get("prompts", {}).get(key)
        or get_default_prompt(f"router_{key}")
    )
    return get_prompt(f"router_{key}", agent_name="router", fallback=fallback, **kwargs)


def analyse_request_node(state: RouterAgentState) -> dict:
    """
    LLM node — determines required_agents, parallel_safe flag, and priority
    from the raw user request.

    Prompt resolution: Langfuse registry → consumer config override → built-in default.
    """
    t0          = time.monotonic()
    agents      = ", ".join(_agent_list(state))
    sys_prompt  = _p("analyse_request", state, agents=agents)
    user_prompt = f"User request: {state['raw_input']}"

    llm    = get_llm()
    result = call_llm(llm, sys_prompt, user_prompt, node_hint="analyse_request")
    log_llm_call(
        "router_agent", "analyse_request_node",
        os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
        sys_prompt[:200], str(result),
        session_id=state.get("session_id", ""),
        token_usage=get_last_token_usage(),
    )

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "required_agents": result.get("required_agents", ["INTENT_AGENT"]),
        "parallel_safe":   result.get("parallel_safe", False),
        "priority":        result.get("priority", "medium"),
        "status":          ExecutionStatus.RUNNING,
        "current_node":    "analyse_request_node",
        "execution_trace": [build_trace_entry("analyse_request_node", duration_ms, 250)],
        "audit_events":    [make_audit_event(state, "analyse_request_node", "REQUEST_ANALYSED")],
    }
