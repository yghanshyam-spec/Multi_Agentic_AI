"""
agents/workflow/workflows/nodes/sequence_steps_node.py
========================================================
Node function: ``sequence_steps_node``

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


def sequence_steps_node(state):
    t0 = time.monotonic()
    wf = state.get("workflow_definition", {})
    steps = wf.get("steps", wf.get("tasks", []))
    normalised = [{"step_id": s.get("task_id",s.get("step_id",f"S{i+1}")), "title": s.get("title",f"Step {i+1}"),
                   "agent": s.get("agent","REASONING_AGENT"), "description": s.get("description",""),
                   "deps": s.get("deps",[]), "parallel_safe": s.get("parallel_safe",False),
                   "risk": s.get("risk","low"), "inputs": s.get("inputs",{}), "condition": s.get("condition")}
                  for i,s in enumerate(steps)]
    return {"workflow_definition": {**wf, "steps": normalised}, "current_node": "sequence_steps_node",
            "execution_trace": [build_trace_entry("sequence_steps_node", int((time.monotonic()-t0)*1000))]}
