"""
agents/reasoning/workflows/nodes/frame_problem_node.py
========================================================
Node function: ``frame_problem_node``

Single-responsibility node — part of the reasoning LangGraph workflow.
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
from agents.reasoning.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"reasoning_{key}")
    return get_prompt(f"reasoning_{key}", agent_name="reasoning", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"reasoning_{key}")
    return get_prompt(f"reasoning_{key}", agent_name="reasoning", fallback=fb, **kw)


def frame_problem_node(state):
    t0 = time.monotonic()
    sys_p = _p("frame", state, input=state["raw_input"])
    result = call_llm(get_llm(), sys_p, f"Frame: {state['raw_input']}", node_hint="frame_problem")
    log_llm_call("reasoning_agent","frame_problem_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"framed_problem": result, "status": ExecutionStatus.RUNNING, "current_node": "frame_problem_node",
            "execution_trace": [build_trace_entry("frame_problem_node", int((time.monotonic()-t0)*1000), 200)],
            "audit_events": [make_audit_event(state,"frame_problem_node","PROBLEM_FRAMED")]}
