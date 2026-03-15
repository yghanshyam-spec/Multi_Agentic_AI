"""
agents/notification/workflows/nodes/receive_event_node.py
=================================================================
Node function: ``receive_event_node``

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


def receive_event_node(state):
    t0=time.monotonic()
    event=state.get("event_payload") or {"type":"GENERIC","source":"pipeline","details":state.get("raw_input",""),"severity":"medium"}
    return {"normalised_event":event,"event_type":event.get("type","GENERIC"),"status":ExecutionStatus.RUNNING,
            "current_node":"receive_event_node",
            "execution_trace":[build_trace_entry("receive_event_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"receive_event_node",f"EVENT_RECEIVED:{event.get('type')}")]}
