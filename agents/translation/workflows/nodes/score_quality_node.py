"""
agents/translation/workflows/nodes/score_quality_node.py
==========================================================
Node function: ``score_quality_node``

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


def score_quality_node(state: dict) -> dict:
    t0 = time.monotonic()
    sys_p = _p("score_quality", state,
               original=state.get("raw_input", ""),
               back_translated=state.get("back_translated_text", ""))
    result = call_llm(get_llm(), sys_p, "Score translation quality", node_hint="score_quality")
    log_llm_call(_AGENT, "score_quality_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    score = float(result.get("score", 0.85))
    threshold = float(state.get("config", {}).get("quality_threshold", 0.75))
    return {
        "quality_score": score,
        "quality_distortions": result.get("distortions", []),
        "review_required": score < threshold,
        "current_node": "score_quality_node",
        "execution_trace": [build_trace_entry("score_quality_node", int((time.monotonic() - t0) * 1000), llm_tokens=150)],
        "audit_events": [make_audit_event(state, "score_quality_node", f"QUALITY_SCORE:{score:.2f}")],
    }
