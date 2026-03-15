"""
agents/salesforce/workflows/nodes/format_sf_response_node.py
==============================================================
Node function: ``format_sf_response_node``

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


def format_sf_response_node(state):
    t0=time.monotonic()
    sys_p=_p("format_response",state,sf_results=str(state.get("sf_raw_result",{})),user_request=state.get("raw_input",""))
    r=call_llm(get_llm(),sys_p,"Format SF response",node_hint="format_sf_response")
    log_llm_call(_A,"format_sf_response_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"sf_formatted_response":r.get("summary",r.get("raw_response","Query completed.")),
            "current_node":"format_sf_response_node",
            "execution_trace":[build_trace_entry("format_sf_response_node",int((time.monotonic()-t0)*1000),llm_tokens=250)]}
