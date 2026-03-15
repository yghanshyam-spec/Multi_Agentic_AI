"""
agents/reasoning/workflows/nodes/chain_of_thought_node.py
===========================================================
Node function: ``chain_of_thought_node``

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


def chain_of_thought_node(state):
    t0 = time.monotonic()
    sys_p = _p("cot", state, problem=state.get("framed_problem",{}), evidence=state.get("evidence_set",[]))
    result = call_llm(get_llm(), sys_p, f"Reason: {state.get('framed_problem',{}).get('core_question',state['raw_input'])}", node_hint="chain_of_thought")
    log_llm_call("reasoning_agent","chain_of_thought_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    steps = result.get("steps", result.get("result",["No steps"]))
    if isinstance(steps,str): steps = [steps]
    chain = [{"step":i+1,"text":s} for i,s in enumerate(steps)]
    return {"reasoning_chain": chain, "current_node": "chain_of_thought_node",
            "execution_trace": [build_trace_entry("chain_of_thought_node", int((time.monotonic()-t0)*1000), 400)],
            "audit_events": [make_audit_event(state,"chain_of_thought_node","COT_COMPLETE")]}
