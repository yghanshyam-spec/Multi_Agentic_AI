"""
agents/audit/workflows/nodes/redact_pii_node.py
=================================================
Node function: ``redact_pii_node``

Single-responsibility node — part of the audit LangGraph workflow.
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
from agents.audit.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
# (none)

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"audit_{key}")
    return get_prompt(f"audit_{key}", agent_name="audit", fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"audit_{key}")
    return get_prompt(f"audit_{key}", agent_name="audit", fallback=fb, **kw)


def redact_pii_node(state):
    t0 = time.monotonic()
    return {"current_node": "redact_pii_node",
            "execution_trace": [build_trace_entry("redact_pii_node", int((time.monotonic()-t0)*1000))]}
