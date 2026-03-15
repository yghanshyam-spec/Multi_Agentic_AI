"""
agents/api_query/workflows/nodes/manage_auth_node.py
======================================================
Node function: ``manage_auth_node``

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


def manage_auth_node(state):
    t0=time.monotonic()
    auth_cfg=state.get("config",{}).get("api",{}).get("auth",{})
    headers={}
    if auth_cfg.get("type")=="api_key": headers={"Authorization":f"Bearer {auth_cfg.get('key','mock-key')}"}
    elif auth_cfg.get("type")=="oauth2": headers={"Authorization":f"Bearer {auth_cfg.get('access_token','mock-token')}"}
    return {"request_headers":headers,"auth_refreshed":False,"current_node":"manage_auth_node",
            "execution_trace":[build_trace_entry("manage_auth_node",int((time.monotonic()-t0)*1000))]}
