"""
agents/email_handler/workflows/nodes/classify_email_node.py
=============================================================
Node function: ``classify_email_node``

Single-responsibility node — part of the email_handler LangGraph workflow.
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
from agents.email_handler.prompts.defaults import get_default_prompt
from agents.email_handler.tools.mailbox_connector import MailboxConnector

# ── Module-level constants ────────────────────────────────────────────────────
_AGENT = "email_handler_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(key: str, state: dict, **kw) -> str:
    override = state.get("config", {}).get("prompts", {}).get(key)
    fallback = override or get_default_prompt(f"email_handler_{key}")
    return get_prompt(f"email_handler_{key}", agent_name=_AGENT, fallback=fallback, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"email_handler_{key}")
    return get_prompt(f"email_handler_{key}", agent_name="email_handler", fallback=fb, **kw)


def classify_email_node(state: dict) -> dict:
    t0 = time.monotonic()
    sys_p = _p("classify", state, parsed_email=str(state.get("parsed_email", {})))
    result = call_llm(get_llm(), sys_p, "Classify email category", node_hint="classify_email")
    log_llm_call(_AGENT, "classify_email_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    category = result.get("category", "OTHER")
    return {
        "email_category": category,
        "email_classification": result,
        "requires_human": result.get("requires_human", False),
        "classification_confidence": float(result.get("confidence", 0.8)),
        "current_node": "classify_email_node",
        "execution_trace": [build_trace_entry("classify_email_node", int((time.monotonic() - t0) * 1000), llm_tokens=150)],
        "audit_events": [make_audit_event(state, "classify_email_node", f"EMAIL_CLASSIFIED:{category}")],
    }
