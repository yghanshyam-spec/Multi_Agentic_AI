"""
agents/notification/workflows/nodes/track_engagement_node.py
====================================================================
Node function: ``track_engagement_node``

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


def track_engagement_node(state):
    t0=time.monotonic()
    receipt=state.get("dispatch_result",{})
    tracking={"notification_id":receipt.get("notification_id"),"status":receipt.get("status"),
               "channel":state.get("selected_channel"),"sent_at":receipt.get("sent_at"),
               "event_type":state.get("event_type"),"priority":state.get("notification_priority")}
    resp=build_agent_response(state,payload={"tracking":tracking,"recipients_notified":len(state.get("recipients",[])),
        "channel":state.get("selected_channel"),"message_preview":state.get("crafted_message","")[:100],
        "duplicate_suppressed":state.get("is_duplicate",False)},confidence_score=0.95)
    return {"engagement_tracking":tracking,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"track_engagement_node",
            "execution_trace":[build_trace_entry("track_engagement_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"track_engagement_node","ENGAGEMENT_TRACKED")]}
