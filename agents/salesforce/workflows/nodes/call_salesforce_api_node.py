"""
agents/salesforce/workflows/nodes/call_salesforce_api_node.py
===============================================================
Node function: ``call_salesforce_api_node``

Single-responsibility node — part of the salesforce LangGraph workflow.
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


def call_salesforce_api_node(state):
    t0=time.monotonic()
    conn=SalesforceConnector(state.get("config",{}).get("salesforce",{}))
    if state.get("sf_operation_type","query")=="query":
        result=conn.query(state.get("soql_query","SELECT Id FROM Lead LIMIT 1"))
    else:
        result={"records":[],"totalSize":0,"done":True}
    return {"sf_raw_result":result,"sf_error":None,"current_node":"call_salesforce_api_node",
            "execution_trace":[build_trace_entry("call_salesforce_api_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"call_salesforce_api_node",f"SF_API_CALLED:rows={result.get('totalSize')}")]}
