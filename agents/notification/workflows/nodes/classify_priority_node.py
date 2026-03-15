"""
agents/notification/workflows/nodes/classify_priority_node.py
=====================================================================
Node function: ``classify_priority_node``

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


def classify_priority_node(state):
    t0=time.monotonic()
    recip=state.get("recipients",[{}])[0]
    sys_p=_p("classify_priority",state,event_details=str(state.get("enriched_event",{})),recipient_role=recip.get("role",""))
    r=call_llm(get_llm(),sys_p,"Classify priority",node_hint="classify_priority")
    log_llm_call(_A,"classify_priority_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    priority=r.get("priority","medium")
    return {"notification_priority":priority,"send_immediately":r.get("send_immediately",True),
            "batch_eligible":r.get("batch_eligible",False),"current_node":"classify_priority_node",
            "execution_trace":[build_trace_entry("classify_priority_node",int((time.monotonic()-t0)*1000),llm_tokens=100)]}
