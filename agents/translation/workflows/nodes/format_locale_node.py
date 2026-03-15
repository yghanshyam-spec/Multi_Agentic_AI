"""
agents/translation/workflows/nodes/format_locale_node.py
==========================================================
Node function: ``format_locale_node``

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

def _to_float(v, default: float = 0.9) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return default


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


def format_locale_node(state: dict) -> dict:
    t0 = time.monotonic()
    locale = state.get("target_locale", state.get("target_language", "de"))
    sys_p = _p("format_locale", state,
               target_locale=locale,
               translated_text=state.get("translated_text", ""))
    result = call_llm(get_llm(), sys_p, "Apply locale formatting", node_hint="format_locale")
    log_llm_call(_AGENT, "format_locale_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    from shared import build_agent_response
    final_text = result.get("formatted_text", state.get("translated_text", ""))
    response = build_agent_response(state, payload={
        "translated_text": final_text,
        "source_language": state.get("source_language"),
        "target_language": state.get("target_language"),
        "quality_score": state.get("quality_score"),
        "review_required": state.get("review_required", False),
    }, confidence_score=_to_float(state.get("quality_score", 0.85)))
    return {
        "final_translated_text": final_text,
        "agent_response": dict(response),
        "status": ExecutionStatus.COMPLETED,
        "current_node": "format_locale_node",
        "execution_trace": [build_trace_entry("format_locale_node", int((time.monotonic() - t0) * 1000), llm_tokens=100)],
        "audit_events": [make_audit_event(state, "format_locale_node", f"LOCALE_FORMATTED:{locale}")],
    }
