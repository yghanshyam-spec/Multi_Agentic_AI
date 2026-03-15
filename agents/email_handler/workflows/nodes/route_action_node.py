"""
agents/email_handler/workflows/nodes/route_action_node.py
===========================================================
Node function: ``route_action_node``

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


def route_action_node(state: dict) -> dict:
    t0 = time.monotonic()
    sys_p = _p("route", state,
               classification=str(state.get("email_classification", {})),
               entities=str(state.get("email_entities", {})))
    result = call_llm(get_llm(), sys_p, "Route email action", node_hint="route_action")
    log_llm_call(_AGENT, "route_action_node", os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")), sys_p[:200], str(result), state.get("session_id", ""), token_usage=get_last_token_usage())
    return {
        "action_route": result.get("route", "AUTO_REPLY"),
        "routing_rationale": result.get("rationale", ""),
        "current_node": "route_action_node",
        "execution_trace": [build_trace_entry("route_action_node", int((time.monotonic() - t0) * 1000), llm_tokens=100)],
    }
