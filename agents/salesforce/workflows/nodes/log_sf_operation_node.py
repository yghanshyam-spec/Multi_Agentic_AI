"""
agents/salesforce/workflows/nodes/log_sf_operation_node.py
============================================================
Node function: ``log_sf_operation_node``

Single-responsibility node — part of the salesforce LangGraph workflow.
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
from agents.salesforce.prompts.defaults import get_default_prompt
from agents.salesforce.tools.sf_connector import SalesforceConnector

# ── Module-level constants ────────────────────────────────────────────────────
_A="salesforce_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"sf_{k}")
    return get_prompt(f"sf_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"salesforce_{key}")
    return get_prompt(f"salesforce_{key}", agent_name="salesforce", fallback=fb, **kw)


def log_sf_operation_node(state):
    t0=time.monotonic()
    sys_p=_p("log_operation",state,operation_type=state.get("sf_operation_type","query"),
             sf_object=state.get("sf_object",""),record_count=state.get("sf_raw_result",{}).get("totalSize",0))
    r=call_llm(get_llm(),sys_p,"Log SF operation",node_hint="log_sf_operation")
    log_llm_call(_A,"log_sf_operation_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    resp=build_agent_response(state,payload={"formatted_response":state.get("sf_formatted_response",""),
        "soql":state.get("soql_query",""),"records_retrieved":state.get("sf_raw_result",{}).get("totalSize",0),
        "operation":state.get("sf_operation_type"),"object":state.get("sf_object")},confidence_score=0.9)
    return {"sf_audit_entry":r.get("audit_entry",{}),"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"log_sf_operation_node",
            "execution_trace":[build_trace_entry("log_sf_operation_node",int((time.monotonic()-t0)*1000),llm_tokens=100)],
            "audit_events":[make_audit_event(state,"log_sf_operation_node","SF_OPERATION_LOGGED")]}
