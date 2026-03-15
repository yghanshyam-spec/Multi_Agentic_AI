"""
agents/execution/workflows/nodes/report_execution_node.py
===========================================================
Node function: ``report_execution_node``

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


def report_execution_node(state):
    t0 = time.monotonic()
    sys_p = _p("report", state, log={"plan":state.get("execution_plan",{}),"output":state.get("execution_output",{}),"verified":state.get("verification_result",{})})
    result = call_llm(get_llm(), sys_p, "Generate execution report", node_hint="report_execution")
    log_llm_call("execution_agent","report_execution_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    summary = result.get("summary", state.get("execution_output",{}).get("stdout","Execution completed."))
    response = build_agent_response(state, payload={"execution_report":summary,"script":state.get("execution_plan",{}).get("script","")[:80],
        "exit_code":state.get("execution_output",{}).get("exit_code",0),"rows_affected":state.get("execution_output",{}).get("rows_affected",0),
        "verification":state.get("verification_result",{}),"rollback_executed":state.get("rollback_needed",False)}, confidence_score=0.97)
    return {"execution_report": summary, "agent_response": dict(response), "status": ExecutionStatus.COMPLETED,
            "current_node": "report_execution_node",
            "execution_trace": [build_trace_entry("report_execution_node", int((time.monotonic()-t0)*1000), 150)],
            "audit_events": [make_audit_event(state,"report_execution_node","EXECUTION_COMPLETE")]}
