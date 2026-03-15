"""
agents/notification/workflows/nodes/craft_message_node.py
=================================================================
Node function: ``craft_message_node``

Single-responsibility node — part of the notification_agent LangGraph workflow.
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


def craft_message_node(state):
    t0=time.monotonic()
    recip=state.get("recipients",[{}])[0]
    sys_p=_p("craft_message",state,event_details=str(state.get("enriched_event",{})),
             recipient_profile=str(recip),channel=state.get("selected_channel","Email"),
             priority=state.get("notification_priority","medium"))
    r=call_llm(get_llm(),sys_p,"Craft notification message",node_hint="craft_message")
    log_llm_call(_A,"craft_message_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    msg=r.get("message",r.get("raw_response",f"Notification: {state.get('raw_input','')}"))
    return {"crafted_message":msg,"current_node":"craft_message_node",
            "execution_trace":[build_trace_entry("craft_message_node",int((time.monotonic()-t0)*1000),llm_tokens=250)]}
