"""
agents/sap/workflows/nodes/handle_sap_exception_node.py
===============================================================
Node function: ``handle_sap_exception_node``

Single-responsibility node — part of the sap_agent LangGraph workflow.
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


def handle_sap_exception_node(state):
    t0=time.monotonic()
    errors=state.get("sap_errors",[])
    if not errors:
        return {"current_node":"handle_sap_exception_node","execution_trace":[build_trace_entry("handle_sap_exception_node",0)]}
    sys_p=_p("handle_exception",state,bapi_name=state.get("selected_bapi",""),
             sap_error=str(errors[0].get("MESSAGE","") if errors else ""))
    r=call_llm(get_llm(),sys_p,"Handle SAP exception",node_hint="handle_sap_exception")
    log_llm_call(_A,"handle_sap_exception_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"sap_exception_diagnosis":r,"sap_escalate_human":r.get("escalate_to_human",False),
            "current_node":"handle_sap_exception_node",
            "execution_trace":[build_trace_entry("handle_sap_exception_node",int((time.monotonic()-t0)*1000),llm_tokens=150)]}
