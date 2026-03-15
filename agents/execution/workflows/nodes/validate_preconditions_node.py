"""
agents/execution/workflows/nodes/validate_preconditions_node.py
=================================================================
Node function: ``validate_preconditions_node``

Single-responsibility node — part of the execution LangGraph workflow.
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


def validate_preconditions_node(state):
    t0 = time.monotonic()
    plan = state.get("execution_plan", {})
    sys_p = _p("preconditions", state, step=plan.get("script",""), env_state={"db_status":"healthy","connections":42,"locks":[]})
    result = call_llm(get_llm(), sys_p, "Validate preconditions", node_hint="validate_preconditions")
    log_llm_call("execution_agent","validate_preconditions_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    safe = result.get("safe_to_execute", True)
    return {"preconditions_ok": safe, "current_node": "validate_preconditions_node",
            "execution_trace": [build_trace_entry("validate_preconditions_node", int((time.monotonic()-t0)*1000), 150)],
            "audit_events": [make_audit_event(state,"validate_preconditions_node",f"PRECONDITION:safe={safe}")]}
