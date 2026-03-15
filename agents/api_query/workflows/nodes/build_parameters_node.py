"""
agents/api_query/workflows/nodes/build_parameters_node.py
===========================================================
Node function: ``build_parameters_node``

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


def build_parameters_node(state):
    t0=time.monotonic()
    spec_paths=state.get("api_spec",{}).get("paths",{})
    endpoint=state.get("selected_endpoint","/companies/search")
    method=state.get("http_method","get").lower()
    param_schema=spec_paths.get(endpoint,{}).get(method,{}).get("parameters",[])
    sys_p=_p("build_params",state,param_schema=json.dumps(param_schema),
             user_intent=state.get("raw_input",""),entities=str(state.get("extracted_entities",{})))
    r=call_llm(get_llm(),sys_p,"Build API parameters",node_hint="build_parameters")
    log_llm_call(_A,"build_parameters_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"request_params":r.get("params",r.get("raw_response",{"name":"Acme"})),"current_node":"build_parameters_node",
            "execution_trace":[build_trace_entry("build_parameters_node",int((time.monotonic()-t0)*1000),llm_tokens=120)]}
