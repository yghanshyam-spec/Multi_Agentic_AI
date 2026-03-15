"""
agents/translation/workflows/nodes/preprocess_text_node.py
============================================================
Node function: ``preprocess_text_node``

Single-responsibility node — part of the translation LangGraph workflow.
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
from agents.translation.prompts.defaults import get_default_prompt


# ── Module-level constants ────────────────────────────────────────────────────
_AGENT = "translation_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key: str, state: dict, **kw) -> str:
    override = state.get("config", {}).get("prompts", {}).get(key)
    fallback = override or get_default_prompt(f"translation_{key}")
    return get_prompt(f"translation_{key}", agent_name=_AGENT, fallback=fallback, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"translation_{key}")
    return get_prompt(f"translation_{key}", agent_name="translation", fallback=fb, **kw)


def preprocess_text_node(state: dict) -> dict:
    t0 = time.monotonic()
    text = state.get("raw_input", "")
    sys_p = _p("preprocess", state, text=text)
    result = call_llm(get_llm(), sys_p, "Identify protected spans", node_hint="preprocess_text")
    log_llm_call(_AGENT, "preprocess_text_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    return {
        "protected_spans": result.get("protected_spans", []),
        "preprocessed_text": result.get("clean_text", text),
        "current_node": "preprocess_text_node",
        "execution_trace": [build_trace_entry("preprocess_text_node", int((time.monotonic() - t0) * 1000), llm_tokens=120)],
        "audit_events": [make_audit_event(state, "preprocess_text_node", "TEXT_PREPROCESSED")],
    }
