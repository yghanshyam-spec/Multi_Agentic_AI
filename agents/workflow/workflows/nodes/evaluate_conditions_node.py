"""
agents/workflow/workflows/nodes/evaluate_conditions_node.py
=============================================================
Node function: ``evaluate_conditions_node``

Single-responsibility node — part of the workflow LangGraph workflow.
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
from agents.workflow.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"workflow_{key}")
    return get_prompt(f"workflow_{key}", agent_name="workflow", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"workflow_{key}")
    return get_prompt(f"workflow_{key}", agent_name="workflow", fallback=fb, **kw)


def evaluate_conditions_node(state):
    t0 = time.monotonic()
    step = state.get("current_step", {})
    cond = step.get("condition") if step else None
    if not cond:
        return {"condition_results": {**state.get("condition_results",{}),"last":True},
                "current_node": "evaluate_conditions_node",
                "execution_trace": [build_trace_entry("evaluate_conditions_node", int((time.monotonic()-t0)*1000))]}
    sys_p = _p("condition", state, condition=cond, state=state.get("step_results",{}))
    result = call_llm(get_llm(), sys_p, f"Evaluate: {cond}", node_hint="evaluate_conditions")
    return {"condition_results": {**state.get("condition_results",{}), step.get("step_id","last"): result},
            "current_node": "evaluate_conditions_node",
            "execution_trace": [build_trace_entry("evaluate_conditions_node", int((time.monotonic()-t0)*1000), 100)]}
