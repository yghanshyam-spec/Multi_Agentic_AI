"""
agents/intent/workflows/nodes/request_clarification_node.py
=============================================================
Node function: ``request_clarification_node``

Single-responsibility node — part of the intent LangGraph workflow.
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


def request_clarification_node(state: IntentAgentState) -> dict:
    t0 = time.monotonic()
    intents = [i.get("intent") for i in state.get("detected_intents", [])]
    sys_p = _p("clarify", state, intents=intents)
    result = call_llm(get_llm(), sys_p, f"Ambiguous: {state.get('normalised_input','')}", node_hint="request_clarification")
    return {"clarification_q": result.get("question", result.get("raw_response","Could you clarify?")),
            "current_node": "request_clarification_node",
            "execution_trace": [build_trace_entry("request_clarification_node", int((time.monotonic()-t0)*1000), 100)]}
