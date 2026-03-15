"""
agents/mcp_invoker/workflows/nodes/select_mcp_tool_node.py
============================================================
Node function: ``select_mcp_tool_node``

Single-responsibility node — part of the mcp_invoker LangGraph workflow.
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


def select_mcp_tool_node(state):
    t0=time.monotonic()
    manifest=json.dumps(state.get("mcp_capabilities",{}).get("tools",[]),indent=2)
    sys_p=_p("select_tool",state,tool_manifest=manifest,user_task=state.get("raw_input",""))
    r=call_llm(get_llm(),sys_p,"Select MCP tool",node_hint="select_mcp_tool")
    log_llm_call(_A,"select_mcp_tool_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"selected_tool":r.get("tool_name","web_search"),"tool_parameters":r.get("parameters",{}),"tool_rationale":r.get("rationale",""),
            "current_node":"select_mcp_tool_node",
            "execution_trace":[build_trace_entry("select_mcp_tool_node",int((time.monotonic()-t0)*1000),llm_tokens=200)]}
