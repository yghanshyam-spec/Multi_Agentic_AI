"""
agents/api_query/workflows/nodes/select_endpoint_node.py
==========================================================
Node function: ``select_endpoint_node``

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


def select_endpoint_node(state):
    t0=time.monotonic()
    sys_p=_p("select_endpoint",state,user_intent=state.get("raw_input",""),
             endpoint_catalogue=json.dumps(state.get("endpoint_catalogue",[]),indent=2))
    r=call_llm(get_llm(),sys_p,"Select API endpoint",node_hint="select_endpoint")
    log_llm_call(_A,"select_endpoint_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"selected_endpoint":r.get("endpoint_path","/companies/search"),"http_method":r.get("method","GET"),
            "parameters_needed":r.get("parameters_needed",[]),"current_node":"select_endpoint_node",
            "execution_trace":[build_trace_entry("select_endpoint_node",int((time.monotonic()-t0)*1000),llm_tokens=150)]}
