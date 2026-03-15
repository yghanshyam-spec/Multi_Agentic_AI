"""
agents/router/workflows/nodes/orchestrate_response_node.py
============================================================
Node: ``orchestrate_response_node``

LLM node — synthesises all activated-agent results into a single coherent
response and sets agent_response to a standard AgentResponse envelope.

Tracing & prompts: shared.langfuse_manager only (via shared.common).
No local langfuse_client or prompt_manager.
"""
from __future__ import annotations
import os
import time

from shared.common import (
    get_llm, call_llm, get_prompt, log_llm_call,
    make_audit_event, build_trace_entry,
    build_agent_response, ExecutionStatus, get_last_token_usage,
)
from shared.state import RouterAgentState, AgentResponse
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


def orchestrate_response_node(state: RouterAgentState) -> dict:
    """
    LLM node — synthesises all agent results into one coherent response.

    Sets ``agent_response`` to a standard AgentResponse TypedDict so the
    pipeline can extract a structured output envelope.

    Prompt resolution: Langfuse registry → consumer config override → built-in default.
    """
    t0          = time.monotonic()
    partial     = state.get("partial_results", [])
    sys_prompt  = _p("orchestrate_response", state)
    user_prompt = (
        f"Original request: {state['raw_input']}\n"
        f"Agent results: {partial}"
    )

    llm    = get_llm()
    result = call_llm(llm, sys_prompt, user_prompt, node_hint="orchestrate_response")
    log_llm_call(
        "router_agent", "orchestrate_response_node",
        os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),
        sys_prompt[:200], str(result),
        session_id=state.get("session_id", ""),
        token_usage=get_last_token_usage(),
    )

    summary     = result.get("summary", "All agents completed their assigned tasks successfully.")
    duration_ms = int((time.monotonic() - t0) * 1000)

    # Build the standard AgentResponse envelope
    agent_response: AgentResponse = build_agent_response(
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
        "agent_response":  dict(agent_response),
        "status":          ExecutionStatus.COMPLETED,
        "current_node":    "orchestrate_response_node",
        "execution_trace": [build_trace_entry("orchestrate_response_node", duration_ms, 300)],
        "audit_events":    [make_audit_event(
            state, "orchestrate_response_node", "ORCHESTRATION_COMPLETE"
        )],
    }
