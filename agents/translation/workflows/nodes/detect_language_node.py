"""
agents/translation/workflows/nodes/detect_language_node.py
============================================================
Node function: ``detect_language_node``

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


def detect_language_node(state: dict) -> dict:
    t0 = time.monotonic()
    text = state.get("raw_input", "")
    sys_p = _p("detect_language", state, text=text[:500])
    result = call_llm(get_llm(), sys_p, "Detect language", node_hint="detect_language")
    log_llm_call(_AGENT, "detect_language_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    detected = result.get("detected_language", "en")
    return {
        "detected_language": detected,
        "source_language": state.get("source_language") or detected,
        "status": ExecutionStatus.RUNNING,
        "current_node": "detect_language_node",
        "execution_trace": [build_trace_entry("detect_language_node", int((time.monotonic() - t0) * 1000), llm_tokens=80)],
        "audit_events": [make_audit_event(state, "detect_language_node", f"LANG_DETECTED:{detected}")],
    }
