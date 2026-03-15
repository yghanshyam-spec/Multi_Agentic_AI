"""
agents/planner/workflows/nodes/estimate_resources_node.py
===========================================================
Node function: ``estimate_resources_node``

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


def estimate_resources_node(state):
    t0 = time.monotonic()
    sys_p = _p("estimate", state, plan=state.get("task_graph",[]))
    result = call_llm(get_llm(), sys_p, f"Estimate: {state.get('task_graph',[])}", node_hint="estimate_resources")
    return {"resource_estimates": result, "current_node": "estimate_resources_node",
            "execution_trace": [build_trace_entry("estimate_resources_node", int((time.monotonic()-t0)*1000), 180)]}
