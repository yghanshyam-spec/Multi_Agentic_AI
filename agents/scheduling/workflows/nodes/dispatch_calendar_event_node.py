"""
agents/scheduling/workflows/nodes/dispatch_calendar_event_node.py
=========================================================================
Node function: ``dispatch_calendar_event_node``

Single-responsibility node — part of the scheduling_agent LangGraph workflow.
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


def dispatch_calendar_event_node(state):
    t0=time.monotonic()
    conn=CalendarConnector(state.get("config",{}).get("calendar",{}))
    action=state.get("sched_action","create")
    if action=="create":
        result=conn.create_event({"subject":state.get("event_subject","Meeting"),
            "body":state.get("event_body",""),"participants":state.get("sched_participants",[]),
            "start":state.get("preferred_time",""),"duration":state.get("duration_minutes",60)})
    else:
        result={"status":"NO_OP","action":action}
    return {"calendar_result":result,"current_node":"dispatch_calendar_event_node",
            "execution_trace":[build_trace_entry("dispatch_calendar_event_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"dispatch_calendar_event_node",f"CALENDAR_EVENT:{action}")]}
