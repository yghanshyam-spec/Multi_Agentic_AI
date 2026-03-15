"""
agents/reasoning/workflows/nodes/call_tool_node.py
====================================================
Node function: ``call_tool_node``

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


def call_tool_node(state):
    t0 = time.monotonic()
    tool_results = [
        {"tool":"db_query","result":"EXPLAIN ANALYZE shows Seq Scan on orders (cost=0..89432)"},
        {"tool":"log_search","result":"Deployment v2.3.1 at 14:15 UTC. Table size grew 4x."},
        {"tool":"metrics","result":"DB CPU 94%, query duration P99=4200ms since 14:30 UTC"},
    ]
    return {"tool_results": tool_results, "current_node": "call_tool_node",
            "execution_trace": [build_trace_entry("call_tool_node", int((time.monotonic()-t0)*1000))]}
