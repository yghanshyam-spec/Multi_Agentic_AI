"""
agents/sap/workflows/nodes/select_bapi_node.py
======================================================
Node function: ``select_bapi_node``

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


def select_bapi_node(state):
    t0=time.monotonic()
    module=state.get("sap_module","MM")
    catalogue=BAPI_CATALOGUE.get(module,["BAPI_TRANSACTION_COMMIT"])
    sys_p=_p("select_bapi",state,sap_module=module,operation=state.get("sap_operation","query"),
             key_fields=str(state.get("sap_key_fields",{})),bapi_catalogue=",".join(catalogue))
    r=call_llm(get_llm(),sys_p,"Select BAPI",node_hint="select_bapi")
    log_llm_call(_A,"select_bapi_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    bapi=r.get("bapi_name",catalogue[0] if catalogue else "BAPI_TRANSACTION_COMMIT")
    return {"selected_bapi":bapi,"bapi_import_params":r.get("import_params",{}),"current_node":"select_bapi_node",
            "execution_trace":[build_trace_entry("select_bapi_node",int((time.monotonic()-t0)*1000),llm_tokens=150)]}
