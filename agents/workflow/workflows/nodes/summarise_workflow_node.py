"""
agents/workflow/workflows/nodes/summarise_workflow_node.py
============================================================
Node function: ``summarise_workflow_node``

Single-responsibility node — part of the workflow LangGraph workflow.
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


def summarise_workflow_node(state):
    t0 = time.monotonic()
    wf = state.get("workflow_definition", {})
    completed = state.get("completed_steps", [])
    sys_p = _p("summarise", state, name=wf.get("name","Workflow"),
               steps=[s.get("title") for s in completed], outputs=state.get("step_results",{}))
    result = call_llm(get_llm(), sys_p, "Generate workflow summary", node_hint="summarise_workflow")
    log_llm_call("workflow_agent","summarise_workflow_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    summary = result.get("summary","Workflow completed successfully.")
    response = build_agent_response(state, payload={"workflow_name":wf.get("name","Workflow"),
        "steps_completed":len(completed),"summary":summary,"step_results":state.get("step_results",{})},confidence_score=0.90)
    return {"workflow_summary": summary, "agent_response": dict(response), "status": ExecutionStatus.COMPLETED,
            "current_node": "summarise_workflow_node",
            "execution_trace": [build_trace_entry("summarise_workflow_node", int((time.monotonic()-t0)*1000), 200)],
            "audit_events": [make_audit_event(state,"summarise_workflow_node","WORKFLOW_COMPLETE")]}
