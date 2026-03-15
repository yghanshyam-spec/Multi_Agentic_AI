"""
agents/notification/workflows/nodes/select_channel_node.py
==================================================================
Node function: ``select_channel_node``

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


def select_channel_node(state):
    t0=time.monotonic()
    recip=state.get("recipients",[{}])[0]
    sys_p=_p("select_channel",state,user_preferences=str(state.get("config",{}).get("user_preferences",{})),
             priority=state.get("notification_priority","medium"),current_time=utc_now())
    r=call_llm(get_llm(),sys_p,"Select channel",node_hint="select_channel")
    log_llm_call(_A,"select_channel_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    channel=r.get("primary_channel","Email")
    return {"selected_channel":channel,"fallback_channel":r.get("fallback_channel","Slack"),
            "current_node":"select_channel_node",
            "execution_trace":[build_trace_entry("select_channel_node",int((time.monotonic()-t0)*1000),llm_tokens=100)]}
