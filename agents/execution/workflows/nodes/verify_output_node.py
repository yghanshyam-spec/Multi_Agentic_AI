"""
agents/execution/workflows/nodes/verify_output_node.py
========================================================
Node function: ``verify_output_node``

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


def verify_output_node(state):
    t0 = time.monotonic()
    plan = state.get("execution_plan", {})
    output = state.get("execution_output", {})
    sys_p = _p("verify", state, expected=plan.get("expected_outcome","success"), actual=output)
    result = call_llm(get_llm(), sys_p, "Verify output", node_hint="verify_output")
    action = result.get("action","continue")
    return {"verification_result": result, "rollback_needed": action=="rollback", "current_node": "verify_output_node",
            "execution_trace": [build_trace_entry("verify_output_node", int((time.monotonic()-t0)*1000), 150)]}
