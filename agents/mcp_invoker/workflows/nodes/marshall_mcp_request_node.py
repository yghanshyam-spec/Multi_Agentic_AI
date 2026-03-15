"""
agents/mcp_invoker/workflows/nodes/marshall_mcp_request_node.py
=================================================================
Node function: ``marshall_mcp_request_node``

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


def marshall_mcp_request_node(state):
    t0=time.monotonic()
    from shared import new_id
    req={"jsonrpc":"2.0","method":"tools/call","id":new_id("req"),
         "params":{"name":state.get("selected_tool",""),"arguments":state.get("tool_parameters",{})}}
    return {"mcp_request":req,"current_node":"marshall_mcp_request_node",
            "execution_trace":[build_trace_entry("marshall_mcp_request_node",int((time.monotonic()-t0)*1000))]}
