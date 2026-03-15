"""
agents/audit/workflows/nodes/generate_audit_report_node.py
============================================================
Node function: ``generate_audit_report_node``

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


def generate_audit_report_node(state):
    t0 = time.monotonic()
    events = state.get("normalised_events", [])
    sys_p = _p("report", state, logs={"events":events,"policy_results":state.get("policy_results",[]),"anomalies":state.get("anomalies",[])})
    result = call_llm(get_llm(), sys_p, "Generate audit report", node_hint="generate_audit_report")
    log_llm_call("audit_agent","generate_audit_report_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    violations = sum(len(r.get("result",{}).get("violations",[])) for r in state.get("policy_results",[]))
    score = 1.0 if violations==0 else max(0, 1.0-(violations*0.1))
    response = build_agent_response(state, payload={"total_events":len(events),"policy_violations":violations,
        "anomalies_detected":len(state.get("anomalies",[])),"compliance_score":score,
        "langfuse_trace_id":state.get("langfuse_trace_id"),
        "agents_audited":list({e.get("agent_type") for e in events}),
        "hitl_checkpoints":sum(1 for e in events if "HITL" in e.get("action","")),
        "detailed_report":result}, confidence_score=0.98)
    return {"audit_report": result, "compliance_score": score, "agent_response": dict(response),
            "status": ExecutionStatus.COMPLETED, "current_node": "generate_audit_report_node",
            "execution_trace": [build_trace_entry("generate_audit_report_node", int((time.monotonic()-t0)*1000), 200)]}
