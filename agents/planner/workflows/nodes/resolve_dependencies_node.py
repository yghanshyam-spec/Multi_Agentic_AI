"""
agents/planner/workflows/nodes/resolve_dependencies_node.py
=============================================================
Node function: ``resolve_dependencies_node``

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


def resolve_dependencies_node(state):
    t0 = time.monotonic()
    tasks = state.get("task_graph", [])
    task_ids = [t.get("task_id",f"T{i}") for i,t in enumerate(tasks)]
    deps_map = {t.get("task_id",f"T{i}"): t.get("deps",[]) for i,t in enumerate(tasks)}
    visited, order = set(), []
    def visit(tid):
        if tid in visited: return
        visited.add(tid)
        for dep in deps_map.get(tid, []): visit(dep)
        order.append(tid)
    for tid in task_ids: visit(tid)
    return {"execution_order": order, "current_node": "resolve_dependencies_node",
            "execution_trace": [build_trace_entry("resolve_dependencies_node", int((time.monotonic()-t0)*1000))]}
