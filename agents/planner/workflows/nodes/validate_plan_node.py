"""
agents/planner/workflows/nodes/validate_plan_node.py
======================================================
Node function: ``validate_plan_node``

Single-responsibility node — part of the planner LangGraph workflow.
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
from agents.planner.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"planner_{key}")
    return get_prompt(f"planner_{key}", agent_name="planner", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"planner_{key}")
    return get_prompt(f"planner_{key}", agent_name="planner", fallback=fb, **kw)


def validate_plan_node(state):
    t0 = time.monotonic()
    full = {"tasks": state.get("task_graph",[]), "order": state.get("execution_order",[]),
            "assignments": state.get("agent_assignments",{}), "resources": state.get("resource_estimates",{})}
    sys_p = _p("validate", state, plan=full)
    result = call_llm(get_llm(), sys_p, f"Validate: {full}", node_hint="validate_plan")
    log_llm_call("planner_agent","validate_plan_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"validated_plan": result, "current_node": "validate_plan_node",
            "execution_trace": [build_trace_entry("validate_plan_node", int((time.monotonic()-t0)*1000), 200)],
            "audit_events": [make_audit_event(state,"validate_plan_node",f"PLAN_VALID:{result.get('valid',True)}")]}
