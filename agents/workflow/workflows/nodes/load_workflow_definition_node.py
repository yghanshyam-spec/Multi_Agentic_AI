"""
agents/workflow/workflows/nodes/load_workflow_definition_node.py
==================================================================
Node function: ``load_workflow_definition_node``

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


def load_workflow_definition_node(state):
    t0 = time.monotonic()
    wf = state.get("working_memory",{}).get("workflow_plan") or \
         {"name":"Incident Response Workflow","steps":state.get("working_memory",{}).get("tasks",[])}
    return {"workflow_definition": wf, "current_step_index": 0, "workflow_status": "RUNNING",
            "status": ExecutionStatus.RUNNING, "current_node": "load_workflow_definition_node",
            "execution_trace": [build_trace_entry("load_workflow_definition_node", int((time.monotonic()-t0)*1000))],
            "audit_events": [make_audit_event(state,"load_workflow_definition_node","WORKFLOW_LOADED")]}
