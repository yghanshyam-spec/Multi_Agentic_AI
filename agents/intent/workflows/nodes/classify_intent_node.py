"""
agents/intent/workflows/nodes/classify_intent_node.py
=======================================================
Node function: ``classify_intent_node``

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


def classify_intent_node(state: IntentAgentState) -> dict:
    t0 = time.monotonic()
    sys_p = _p("classify", state)
    user_p = f"User request: {state.get('normalised_input', state['raw_input'])}"
    result = call_llm(get_llm(), sys_p, user_p, node_hint="classify_intent")
    log_llm_call("intent_agent", "classify_intent_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id",""), token_usage=get_last_token_usage())
    intents = result.get("intents", [{"intent": "REASON", "confidence": 0.9}])
    primary = result.get("primary_intent", intents[0]["intent"] if intents else "REASON")
    return {"detected_intents": intents, "primary_intent": primary, "current_node": "classify_intent_node",
            "execution_trace": [build_trace_entry("classify_intent_node", int((time.monotonic()-t0)*1000), 200)],
            "audit_events": [make_audit_event(state, "classify_intent_node", f"INTENT:{primary}")]}
