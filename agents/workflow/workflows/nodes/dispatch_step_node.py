"""
agents/workflow/workflows/nodes/dispatch_step_node.py
=======================================================
Node function: ``dispatch_step_node``

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


def dispatch_step_node(state):
    t0 = time.monotonic()
    wf = state.get("workflow_definition", {})
    steps = wf.get("steps", [])
    idx = state.get("current_step_index", 0)
    if idx >= len(steps):
        return {"workflow_status": "STEPS_COMPLETE", "current_node": "dispatch_step_node",
                "execution_trace": [build_trace_entry("dispatch_step_node", int((time.monotonic()-t0)*1000))]}
    step = steps[idx]
    result = {"step_id": step["step_id"], "agent": step["agent"], "title": step["title"],
              "status": "COMPLETED", "output": f"Step '{step['title']}' completed by {step['agent']}", "timestamp": utc_now()}
    current = dict(state.get("step_results", {}))
    current[step["step_id"]] = result
    return {"current_step": step, "current_step_index": idx+1, "step_results": current,
            "completed_steps": [result], "current_node": "dispatch_step_node",
            "execution_trace": [build_trace_entry("dispatch_step_node", int((time.monotonic()-t0)*1000))],
            "audit_events": [make_audit_event(state,"dispatch_step_node",f"DISPATCHED:{step['step_id']}")]}
