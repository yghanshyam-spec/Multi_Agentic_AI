"""
agents/notification/workflows/nodes/deduplicate_notification_node.py
============================================================================
Node function: ``deduplicate_notification_node``

Single-responsibility node — part of the notification_agent LangGraph workflow.
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
from agents.notification.prompts.defaults import get_default_prompt
from agents.notification.tools.channel_dispatcher import NotificationDispatcher, DeduplicatorStore

# ── Module-level constants ────────────────────────────────────────────────────
_A="notification"; _DEDUP=DeduplicatorStore()

# ── Tool instances ────────────────────────────────────────────────────────────
_DEDUP = DeduplicatorStore()

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"notif_{k}")
    return get_prompt(f"notif_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"notification_{key}")
    return get_prompt(f"notification_{key}", agent_name="notification", fallback=fb, **kw)


def deduplicate_notification_node(state):
    t0=time.monotonic()
    recip=state.get("recipients",[{}])[0]
    window=int(state.get("config",{}).get("dedup_window_minutes",60))
    is_dup=_DEDUP.is_duplicate(recip.get("user_id",""),state.get("event_type",""),window)
    return {"is_duplicate":is_dup,"current_node":"deduplicate_notification_node",
            "execution_trace":[build_trace_entry("deduplicate_notification_node",int((time.monotonic()-t0)*1000))]}
