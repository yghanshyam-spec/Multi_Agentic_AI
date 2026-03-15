"""
agents/planner/workflows/nodes/decompose_tasks_node.py
========================================================
Node function: ``decompose_tasks_node``

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


def decompose_tasks_node(state):
    t0 = time.monotonic()
    goal = state.get("goal_analysis", {})
    sys_p = _p("decompose", state, objective=goal.get("objective",state["raw_input"]), constraints=goal.get("constraints",{}))
    result = call_llm(get_llm(), sys_p, f"Decompose: {goal.get('objective',state['raw_input'])}", node_hint="decompose_tasks")
    log_llm_call("planner_agent","decompose_tasks_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    tasks = result if isinstance(result, list) else result.get("result", [])
    if not isinstance(tasks, list): tasks = []
    return {"task_graph": tasks, "current_node": "decompose_tasks_node",
            "execution_trace": [build_trace_entry("decompose_tasks_node", int((time.monotonic()-t0)*1000), 350)]}
