"""
agents/translation/workflows/nodes/load_glossary_node.py
==========================================================
Node function: ``load_glossary_node``

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
try:
    from agents.translation.tools.glossary_store import get_glossary
except ImportError:
    def get_glossary(lang): return {}


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


def load_glossary_node(state: dict) -> dict:
    t0 = time.monotonic()
    domain = state.get("domain", "general")
    src = state.get("source_language", "en")
    tgt = state.get("target_language", "de")
    glossary = get_glossary(domain, src, tgt)
    if not glossary:
        sys_p = _p("load_glossary", state, domain=domain, source_language=src, target_language=tgt)
        result = call_llm(get_llm(), sys_p, "Load domain glossary", node_hint="load_glossary")
        log_llm_call(_AGENT, "load_glossary_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
        glossary = result.get("glossary", {})
    return {
        "glossary": glossary,
        "protected_terms": list(glossary.keys()),
        "current_node": "load_glossary_node",
        "execution_trace": [build_trace_entry("load_glossary_node", int((time.monotonic() - t0) * 1000))],
    }
