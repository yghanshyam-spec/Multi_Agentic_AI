"""
agents/api_query/workflows/nodes/execute_request_node.py
==========================================================
Node function: ``execute_request_node``

Single-responsibility node — part of the api_query LangGraph workflow.
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
from agents.api_query.prompts.defaults import get_default_prompt
from agents.api_query.tools.http_client import HTTPClient

# ── Module-level constants ────────────────────────────────────────────────────
_A="api_query_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"api_{k}")
    return get_prompt(f"api_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"api_query_{key}")
    return get_prompt(f"api_query_{key}", agent_name="api_query", fallback=fb, **kw)


def execute_request_node(state):
    t0=time.monotonic()
    client=HTTPClient(state.get("config",{}).get("api",{}))
    result=client.request(state.get("http_method","GET"),state.get("selected_endpoint",""),
                          params=state.get("request_params",{}),headers=state.get("request_headers",{}))
    has_error=result.get("status",200)>=400
    return {"raw_api_response":result,"api_error":result if has_error else None,"current_node":"execute_request_node",
            "execution_trace":[build_trace_entry("execute_request_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"execute_request_node",f"API_CALLED:{state.get('selected_endpoint')} status={result.get('status')}")]}
