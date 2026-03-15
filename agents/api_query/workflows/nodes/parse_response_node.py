"""
agents/api_query/workflows/nodes/parse_response_node.py
=========================================================
Node function: ``parse_response_node``

Single-responsibility node — part of the api_query LangGraph workflow.
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


def parse_response_node(state):
    t0=time.monotonic()
    raw=state.get("raw_api_response",{})
    sys_p=_p("parse_response",state,raw_response=json.dumps(raw.get("body",{})),
             expected_type=state.get("config",{}).get("expected_type","dict"))
    r=call_llm(get_llm(),sys_p,"Parse API response",node_hint="parse_response")
    log_llm_call(_A,"parse_response_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    parsed=r.get("parsed",raw.get("body",{}))
    resp=build_agent_response(state,payload={"parsed_response":parsed,"endpoint":state.get("selected_endpoint"),
        "http_status":raw.get("status",200)},confidence_score=0.9)
    return {"parsed_response":parsed,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"parse_response_node",
            "execution_trace":[build_trace_entry("parse_response_node",int((time.monotonic()-t0)*1000),llm_tokens=150)]}
