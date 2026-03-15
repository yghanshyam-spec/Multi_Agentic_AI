"""
agents/mcp_invoker/workflows/nodes/unmarshall_mcp_response_node.py
====================================================================
Node function: ``unmarshall_mcp_response_node``

Single-responsibility node — part of the mcp_invoker LangGraph workflow.
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
from agents.mcp_invoker.prompts.defaults import get_default_prompt
from agents.mcp_invoker.tools.mcp_client import MCPClient

# ── Module-level constants ────────────────────────────────────────────────────
_A="mcp_invoker_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"mcp_{k}")
    return get_prompt(f"mcp_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"mcp_invoker_{key}")
    return get_prompt(f"mcp_invoker_{key}", agent_name="mcp_invoker", fallback=fb, **kw)


def unmarshall_mcp_response_node(state):
    t0=time.monotonic()
    raw=state.get("mcp_raw_response",{})
    tool_output=raw.get("result","")
    resp=build_agent_response(state,payload={"tool":state.get("selected_tool"),"output":tool_output,
        "server":state.get("selected_server_id"),"request_id":raw.get("request_id")},confidence_score=0.9)
    return {"tool_output":tool_output,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"unmarshall_mcp_response_node",
            "execution_trace":[build_trace_entry("unmarshall_mcp_response_node",int((time.monotonic()-t0)*1000))]}
