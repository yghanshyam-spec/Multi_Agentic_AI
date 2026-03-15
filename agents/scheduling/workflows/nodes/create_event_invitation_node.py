"""
agents/scheduling/workflows/nodes/create_event_invitation_node.py
=========================================================================
Node function: ``create_event_invitation_node``

Single-responsibility node — part of the scheduling_agent LangGraph workflow.
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
from agents.scheduling.prompts.defaults import get_default_prompt
from agents.scheduling.tools.calendar_connector import CalendarConnector

# ── Module-level constants ────────────────────────────────────────────────────
_A="scheduling"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"sched_{k}")
    return get_prompt(f"sched_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"scheduling_{key}")
    return get_prompt(f"scheduling_{key}", agent_name="scheduling", fallback=fb, **kw)


def create_event_invitation_node(state):
    t0=time.monotonic()
    event_details={"type":state.get("event_type","meeting"),"time":state.get("preferred_time",""),
                   "duration":state.get("duration_minutes",60),"recurrence":state.get("recurrence")}
    sys_p=_p("create_event",state,event_details=str(event_details),
             participants=str(state.get("sched_participants",[])),platform=state.get("platform","Teams"))
    r=call_llm(get_llm(),sys_p,"Create event invitation",node_hint="create_event")
    log_llm_call(_A,"create_event_invitation_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"event_invitation":r,"event_subject":r.get("subject","Meeting"),"event_body":r.get("body",""),
            "current_node":"create_event_invitation_node",
            "execution_trace":[build_trace_entry("create_event_invitation_node",int((time.monotonic()-t0)*1000),llm_tokens=200)]}
