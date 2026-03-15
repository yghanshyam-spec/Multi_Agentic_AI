"""
agents/workflow/workflows/nodes/manage_workflow_error_node.py
===============================================================
Node function: ``manage_workflow_error_node``

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


def manage_workflow_error_node(state):
    t0 = time.monotonic()
    errors = state.get("error_history", [])
    if not errors:
        return {"current_node":"manage_workflow_error_node","execution_trace":[build_trace_entry("manage_workflow_error_node",int((time.monotonic()-t0)*1000))]}
    last = errors[-1]
    sys_p = _p("error", state, step_id=last.get("node","unknown"), error=last.get("error",""), remaining=state.get("workflow_definition",{}).get("steps",[]))
    result = call_llm(get_llm(), sys_p, "Determine recovery", node_hint="manage_workflow_error")
    return {"workflow_status": result.get("action","continue"), "current_node": "manage_workflow_error_node",
            "execution_trace": [build_trace_entry("manage_workflow_error_node", int((time.monotonic()-t0)*1000), 150)]}
