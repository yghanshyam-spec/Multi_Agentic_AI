"""
agents/audit/workflows/nodes/evaluate_policy_node.py
======================================================
Node function: ``evaluate_policy_node``

Single-responsibility node — part of the audit LangGraph workflow.
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


def evaluate_policy_node(state):
    t0 = time.monotonic()
    results = []
    for evt in state.get("normalised_events",[])[:5]:
        sys_p = _p("policy", state, action=evt)
        result = call_llm(get_llm(), sys_p, f"Evaluate: {evt.get('action','')}", node_hint="evaluate_policy")
        results.append({"event_id": evt.get("event_id"), "result": result})
    log_llm_call("audit_agent","evaluate_policy_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),"[policy prompts]",str(len(results))+" evaluations",state.get("session_id",""), token_usage=get_last_token_usage())
    return {"policy_results": results, "current_node": "evaluate_policy_node",
            "execution_trace": [build_trace_entry("evaluate_policy_node", int((time.monotonic()-t0)*1000), 200)]}
