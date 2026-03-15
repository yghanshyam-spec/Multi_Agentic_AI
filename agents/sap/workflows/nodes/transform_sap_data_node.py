"""
agents/sap/workflows/nodes/transform_sap_data_node.py
=============================================================
Node function: ``transform_sap_data_node``

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


def transform_sap_data_node(state):
    t0=time.monotonic()
    sys_p=_p("transform_data",state,sap_data=str(state.get("sap_raw_result",{})))
    r=call_llm(get_llm(),sys_p,"Transform SAP data",node_hint="transform_sap_data")
    log_llm_call(_A,"transform_sap_data_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"sap_transformed_data":r.get("transformed",state.get("sap_raw_result",{})),
            "current_node":"transform_sap_data_node",
            "execution_trace":[build_trace_entry("transform_sap_data_node",int((time.monotonic()-t0)*1000),llm_tokens=150)]}
