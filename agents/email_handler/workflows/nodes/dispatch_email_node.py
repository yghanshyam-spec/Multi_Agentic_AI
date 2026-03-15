"""
agents/email_handler/workflows/nodes/dispatch_email_node.py
=============================================================
Node function: ``dispatch_email_node``

Single-responsibility node — part of the email_handler LangGraph workflow.
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
from agents.email_handler.prompts.defaults import get_default_prompt

def _to_float(v, default: float = 0.9) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return default
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


def dispatch_email_node(state: dict) -> dict:
    t0 = time.monotonic()
    connector = MailboxConnector(state.get("config", {}).get("mailbox", {}))
    receipt = connector.send_reply(
        original_id=state.get("email_id", ""),
        reply_body=state.get("reply_draft", ""),
    )
    response = build_agent_response(state, payload={
        "email_id": state.get("email_id"),
        "category": state.get("email_category"),
        "action_route": state.get("action_route"),
        "reply_sent": True,
        "delivery_receipt": receipt,
    }, confidence_score=_to_float(state.get("classification_confidence", 0.8)))
    return {
        "delivery_receipt": receipt,
        "reply_sent": True,
        "agent_response": dict(response),
        "status": ExecutionStatus.COMPLETED,
        "current_node": "dispatch_email_node",
        "execution_trace": [build_trace_entry("dispatch_email_node", int((time.monotonic() - t0) * 1000))],
        "audit_events": [make_audit_event(state, "dispatch_email_node", f"REPLY_DISPATCHED:{receipt.get('message_id')}")],
    }
