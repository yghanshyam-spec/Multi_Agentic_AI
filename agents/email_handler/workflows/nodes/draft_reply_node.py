"""
agents/email_handler/workflows/nodes/draft_reply_node.py
==========================================================
Node function: ``draft_reply_node``

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


def draft_reply_node(state: dict) -> dict:
    t0 = time.monotonic()
    raw = state.get("raw_email", {})
    sys_p = _p("draft_reply", state,
               original_email=raw.get("body", state.get("raw_input", "")),
               context=str(state.get("parsed_email", {})),
               tone=state.get("config", {}).get("reply_tone", "professional"),
               org_name=state.get("config", {}).get("org_name", "Our Organisation"))
    result = call_llm(get_llm(), sys_p, "Draft email reply", node_hint="draft_reply")
    log_llm_call(_AGENT, "draft_reply_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    draft = result.get("draft", result.get("raw_response", "Thank you for your email. We will respond shortly."))
    return {
        "reply_draft": draft,
        "current_node": "draft_reply_node",
        "execution_trace": [build_trace_entry("draft_reply_node", int((time.monotonic() - t0) * 1000), llm_tokens=300)],
    }
