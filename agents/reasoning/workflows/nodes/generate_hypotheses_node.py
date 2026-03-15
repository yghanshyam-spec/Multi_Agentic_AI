"""
agents/reasoning/workflows/nodes/generate_hypotheses_node.py
==============================================================
Node function: ``generate_hypotheses_node``

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


def generate_hypotheses_node(state):
    t0 = time.monotonic()
    problem = state.get("framed_problem", {})
    sys_p = _p("hypotheses", state, problem=problem)
    result = call_llm(get_llm(), sys_p, f"Hypotheses for: {problem.get('core_question',state['raw_input'])}", node_hint="generate_hypotheses")
    log_llm_call("reasoning_agent","generate_hypotheses_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    hyps = result if isinstance(result,list) else result.get("result",[])
    if not isinstance(hyps,list): hyps = [hyps] if hyps else []
    return {"hypotheses": hyps, "current_node": "generate_hypotheses_node",
            "execution_trace": [build_trace_entry("generate_hypotheses_node", int((time.monotonic()-t0)*1000), 250)]}
