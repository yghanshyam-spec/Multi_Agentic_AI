"""
agents/planner/workflows/nodes/serialise_plan_node.py
=======================================================
Node function: ``serialise_plan_node``

Single-responsibility node — part of the planner LangGraph workflow.
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


def serialise_plan_node(state):
    t0 = time.monotonic()
    plan_id = new_id("plan")
    wp = {"plan_id": plan_id, "objective": state.get("goal_analysis",{}).get("objective",state["raw_input"]),
          "tasks": state.get("task_graph",[]), "execution_order": state.get("execution_order",[]),
          "assignments": state.get("agent_assignments",{}), "resources": state.get("resource_estimates",{}),
          "validation": state.get("validated_plan",{}), "created_at": utc_now()}
    response = build_agent_response(state, payload={"plan_id": plan_id, "objective": wp["objective"],
        "task_count": len(wp["tasks"]), "execution_order": wp["execution_order"], "workflow_plan": wp}, confidence_score=0.93)
    return {"workflow_plan": wp, "plan_id": plan_id, "agent_response": dict(response),
            "status": ExecutionStatus.COMPLETED, "current_node": "serialise_plan_node",
            "execution_trace": [build_trace_entry("serialise_plan_node", int((time.monotonic()-t0)*1000))]}
