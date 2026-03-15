"""
agents/scheduling/workflows/nodes/check_availability_node.py
====================================================================
Node function: ``check_availability_node``

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


def check_availability_node(state):
    t0=time.monotonic()
    conn=CalendarConnector(state.get("config",{}).get("calendar",{}))
    existing=conn.get_events("current_user",{"start":state.get("preferred_time","")})
    sys_p=_p("check_availability",state,existing_events=str(existing),
             requested_time=state.get("preferred_time",""),duration_minutes=state.get("duration_minutes",60))
    r=call_llm(get_llm(),sys_p,"Check availability",node_hint="check_availability")
    log_llm_call(_A,"check_availability_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"calendar_available":r.get("available",True),"scheduling_conflicts":r.get("conflicts",[]),
            "suggested_alternatives":r.get("suggested_alternatives",[]),"existing_events":existing,
            "current_node":"check_availability_node",
            "execution_trace":[build_trace_entry("check_availability_node",int((time.monotonic()-t0)*1000),llm_tokens=100)]}
