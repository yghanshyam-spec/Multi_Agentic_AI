"""
agents/intent/workflows/nodes/aggregate_responses_node.py
===========================================================
Node function: ``aggregate_responses_node``

Single-responsibility node — part of the intent LangGraph workflow.
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
from agents.intent.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.70
INTENT_AGENT_MAP = {
    "REASON": "REASONING_AGENT", "CREATE_PLAN": "PLANNER_AGENT",
    "EXECUTE_WORKFLOW": "WORKFLOW_AGENT", "GENERATE_CONTENT": "GENERATOR_AGENT",
    "COMMUNICATE": "COMMUNICATION_AGENT", "EXECUTE_SCRIPT": "EXECUTION_AGENT",
    "HITL_APPROVAL": "HITL_AGENT", "ROUTE_INTENT": "INTENT_AGENT",
    "GENERAL_CHAT": "COMMUNICATION_AGENT",
}

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"intent_{key}")
    return get_prompt(f"intent_{key}", agent_name="intent", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"intent_{key}")
    return get_prompt(f"intent_{key}", agent_name="intent", fallback=fb, **kw)


def aggregate_responses_node(state: IntentAgentState) -> dict:
    t0 = time.monotonic()
    partials = state.get("partial_results", [])
    sys_p = _p("aggregate", state, results=partials)
    result = call_llm(get_llm(), sys_p, f"Original: {state['raw_input']}\nResults: {partials}", node_hint="aggregate_responses")
    log_llm_call("intent_agent", "aggregate_responses_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id",""), token_usage=get_last_token_usage())
    summary = result.get("summary", result.get("raw_response","Processing completed."))
    response = build_agent_response(state, payload={"primary_intent": state.get("primary_intent"),
        "detected_intents": state.get("detected_intents",[]), "entities": state.get("extracted_entities",{}),
        "sub_tasks": state.get("sub_tasks",[]), "aggregated_summary": summary}, confidence_score=0.91)
    return {"aggregated_results": result, "agent_response": dict(response),
            "status": ExecutionStatus.COMPLETED, "current_node": "aggregate_responses_node",
            "execution_trace": [build_trace_entry("aggregate_responses_node", int((time.monotonic()-t0)*1000), 220)],
            "audit_events": [make_audit_event(state, "aggregate_responses_node", "INTENT_COMPLETE")]}
