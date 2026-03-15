"""
agents/sap/workflows/nodes/call_sap_rfc_node.py
=======================================================
Node function: ``call_sap_rfc_node``

Single-responsibility node — part of the sap_agent LangGraph workflow.
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
from agents.sap.prompts.defaults import get_default_prompt
from agents.sap.tools.rfc_connector import RFCConnector,BAPI_CATALOGUE

# ── Module-level constants ────────────────────────────────────────────────────
_A="sap"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"sap_{k}")
    return get_prompt(f"sap_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"sap_{key}")
    return get_prompt(f"sap_{key}", agent_name="sap", fallback=fb, **kw)


def call_sap_rfc_node(state):
    t0=time.monotonic()
    conn=RFCConnector(state.get("config",{}).get("sap",{}))
    result=conn.call_bapi(state.get("selected_bapi",""),state.get("bapi_import_params",{}))
    return_msgs=result.get("RETURN",[])
    has_error=any(m.get("TYPE")=="E" for m in return_msgs)
    return {"sap_raw_result":result,"sap_return_table":return_msgs,"sap_has_error":has_error,
            "current_node":"call_sap_rfc_node",
            "execution_trace":[build_trace_entry("call_sap_rfc_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"call_sap_rfc_node",f"BAPI_CALLED:{state.get('selected_bapi')}")]}
