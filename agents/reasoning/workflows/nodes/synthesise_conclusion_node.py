"""
agents/reasoning/workflows/nodes/synthesise_conclusion_node.py
================================================================
Node function: ``synthesise_conclusion_node``

Single-responsibility node — part of the reasoning LangGraph workflow.
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


def synthesise_conclusion_node(state):
    t0 = time.monotonic()
    sys_p = _p("conclude", state, reasoning=state.get("reasoning_chain",[]))
    result = call_llm(get_llm(), sys_p, "Synthesise conclusion", node_hint="synthesise_conclusion")
    return {"conclusion": result, "current_node": "synthesise_conclusion_node",
            "execution_trace": [build_trace_entry("synthesise_conclusion_node", int((time.monotonic()-t0)*1000), 200)]}
