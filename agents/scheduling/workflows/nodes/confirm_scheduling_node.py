"""
agents/scheduling/workflows/nodes/confirm_scheduling_node.py
====================================================================
Node function: ``confirm_scheduling_node``

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


def confirm_scheduling_node(state):
    t0=time.monotonic()
    sys_p=_p("confirm",state,action=state.get("sched_action",""),
             event_details=str(state.get("event_invitation",{})),result=str(state.get("calendar_result",{})))
    r=call_llm(get_llm(),sys_p,"Confirm scheduling",node_hint="confirm_scheduling")
    log_llm_call(_A,"confirm_scheduling_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    summary=r.get("confirmation",r.get("raw_response","Event scheduled successfully."))
    resp=build_agent_response(state,payload={"summary":summary,"action":state.get("sched_action"),
        "platform":state.get("platform"),"event_id":state.get("calendar_result",{}).get("event_id"),
        "meeting_url":state.get("calendar_result",{}).get("meeting_url"),
        "participants":state.get("sched_participants",[])},confidence_score=0.9)
    return {"scheduling_summary":summary,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"confirm_scheduling_node",
            "execution_trace":[build_trace_entry("confirm_scheduling_node",int((time.monotonic()-t0)*1000),llm_tokens=150)],
            "audit_events":[make_audit_event(state,"confirm_scheduling_node","SCHEDULING_CONFIRMED")]}
