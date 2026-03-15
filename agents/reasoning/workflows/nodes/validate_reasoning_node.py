"""
agents/reasoning/workflows/nodes/validate_reasoning_node.py
=============================================================
Node function: ``validate_reasoning_node``

Single-responsibility node — part of the reasoning LangGraph workflow.
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
from agents.reasoning.prompts.defaults import get_default_prompt

def _to_float(v, default: float = 0.9) -> float:
    """Safely coerce LLM-returned value to float (handles str, None, etc.)."""
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return default


# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"reasoning_{key}")
    return get_prompt(f"reasoning_{key}", agent_name="reasoning", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"reasoning_{key}")
    return get_prompt(f"reasoning_{key}", agent_name="reasoning", fallback=fb, **kw)


def validate_reasoning_node(state):
    t0 = time.monotonic()
    sys_p = _p("validate", state, chain=state.get("reasoning_chain",[]))
    result = call_llm(get_llm(), sys_p, "Validate reasoning", node_hint="validate_reasoning")
    log_llm_call("reasoning_agent","validate_reasoning_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    conclusion = state.get("conclusion", {})
    response = build_agent_response(state, payload={"framed_problem":state.get("framed_problem",{}),
        "hypotheses":state.get("hypotheses",[]),"reasoning_chain":state.get("reasoning_chain",[]),
        "conclusion":conclusion,"reasoning_valid":result.get("valid",True),"reasoning_issues":result.get("issues",[]),
        "primary_cause":conclusion.get("conclusion",""),"confidence":conclusion.get("confidence",0.9)},
        confidence_score=_to_float(conclusion.get("confidence",0.9)))
    return {"reasoning_valid": result.get("valid",True), "reasoning_issues": result.get("issues",[]),
            "agent_response": dict(response), "status": ExecutionStatus.COMPLETED,
            "current_node": "validate_reasoning_node",
            "execution_trace": [build_trace_entry("validate_reasoning_node", int((time.monotonic()-t0)*1000), 150)],
            "audit_events": [make_audit_event(state,"validate_reasoning_node",f"REASONING_VALID:{result.get('valid',True)}")]}
