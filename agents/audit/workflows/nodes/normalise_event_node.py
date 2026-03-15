"""
agents/audit/workflows/nodes/normalise_event_node.py
======================================================
Node function: ``normalise_event_node``

Single-responsibility node — part of the audit LangGraph workflow.
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
from agents.audit.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"audit_{key}")
    return get_prompt(f"audit_{key}", agent_name="audit", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"audit_{key}")
    return get_prompt(f"audit_{key}", agent_name="audit", fallback=fb, **kw)


def normalise_event_node(state):
    t0 = time.monotonic()
    normalised = [{"event_id":e.get("event_id",new_id("evt")),"timestamp":e.get("timestamp",utc_now()),
        "agent_type":e.get("agent_type","UNKNOWN"),"node_name":e.get("node_name",""),
        "correlation_id":e.get("correlation_id",""),"action":e.get("action",""),
        "policy_ok":e.get("policy_ok",True),"violations":e.get("violations",[])}
        for e in state.get("events_to_process",[])]
    return {"normalised_events": normalised, "current_node": "normalise_event_node",
            "execution_trace": [build_trace_entry("normalise_event_node", int((time.monotonic()-t0)*1000))]}
