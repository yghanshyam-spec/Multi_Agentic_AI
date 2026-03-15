"""
agents/scheduling/workflows/nodes/parse_schedule_intent_node.py
=======================================================================
Node function: ``parse_schedule_intent_node``

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


def parse_schedule_intent_node(state):
    t0=time.monotonic()
    sys_p=_p("parse_intent",state,user_request=state.get("raw_input",""))
    r=call_llm(get_llm(),sys_p,"Parse schedule intent",node_hint="parse_schedule_intent")
    log_llm_call(_A,"parse_schedule_intent_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"sched_action":r.get("action","create"),"event_type":r.get("event_type","meeting"),
            "sched_participants":r.get("participants",[]),"preferred_time":r.get("preferred_time",""),
            "duration_minutes":int(r.get("duration_minutes",60)),"platform":r.get("platform","Teams"),
            "recurrence":r.get("recurrence",None),"status":ExecutionStatus.RUNNING,"current_node":"parse_schedule_intent_node",
            "execution_trace":[build_trace_entry("parse_schedule_intent_node",int((time.monotonic()-t0)*1000),llm_tokens=150)],
            "audit_events":[make_audit_event(state,"parse_schedule_intent_node",f"SCHED_INTENT:{r.get('action')}")]}
