"""
agents/reasoning/workflows/nodes/evaluate_evidence_node.py
============================================================
Node function: ``evaluate_evidence_node``

Single-responsibility node — part of the reasoning LangGraph workflow.
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
from agents.reasoning.prompts.defaults import get_default_prompt


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


def evaluate_evidence_node(state):
    t0 = time.monotonic()
    evidence_set = []
    for hyp in state.get("hypotheses",[])[:3]:
        hyp_id = hyp.get("id","H?") if isinstance(hyp,dict) else "H1"
        sys_p = _p("evidence", state, hypothesis=hyp, evidence=state.get("tool_results",[]))
        result = call_llm(get_llm(), sys_p, f"Evaluate {hyp_id}", node_hint="evaluate_evidence")
        evidence_set.append({"hypothesis_id": hyp_id, "evaluation": result})
    return {"evidence_set": evidence_set, "current_node": "evaluate_evidence_node",
            "execution_trace": [build_trace_entry("evaluate_evidence_node", int((time.monotonic()-t0)*1000), 300)]}
