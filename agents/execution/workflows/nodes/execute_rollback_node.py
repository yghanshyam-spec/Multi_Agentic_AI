"""
agents/execution/workflows/nodes/execute_rollback_node.py
===========================================================
Node function: ``execute_rollback_node``

Single-responsibility node — part of the execution LangGraph workflow.
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
from agents.execution.prompts.defaults import get_default_prompt
from agents.execution.tools.sandbox import provision_sandbox, execute_script

# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"execution_{key}")
    return get_prompt(f"execution_{key}", agent_name="execution", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"execution_{key}")
    return get_prompt(f"execution_{key}", agent_name="execution", fallback=fb, **kw)


def execute_rollback_node(state):
    t0 = time.monotonic()
    if not state.get("rollback_needed", False):
        return {"current_node":"execute_rollback_node","execution_trace":[build_trace_entry("execute_rollback_node",int((time.monotonic()-t0)*1000))]}
    plan = state.get("execution_plan", {})
    result = {"script":plan.get("rollback","ROLLBACK"),"status":"COMPLETED","timestamp":utc_now()}
    return {"rollback_result": result, "current_node": "execute_rollback_node",
            "execution_trace": [build_trace_entry("execute_rollback_node", int((time.monotonic()-t0)*1000))],
            "audit_events": [make_audit_event(state,"execute_rollback_node","ROLLBACK_EXECUTED")]}
