"""
agents/vector_query/workflows/nodes/preprocess_query_node.py
==============================================================
Node function: ``preprocess_query_node``

Single-responsibility node — part of the vector_query LangGraph workflow.
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
from agents.vector_query.prompts.defaults import get_default_prompt
from agents.vector_query.tools.vector_store import VectorStore

# ── Module-level constants ────────────────────────────────────────────────────
_A="vector_query_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
_vs = VectorStore()

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"rag_{k}")
    return get_prompt(f"rag_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"vector_query_{key}")
    return get_prompt(f"vector_query_{key}", agent_name="vector_query", fallback=fb, **kw)


def preprocess_query_node(state):
    t0=time.monotonic()
    q=state.get("raw_input","")
    sys_p=_p("preprocess",state,user_query=q)
    r=call_llm(get_llm(),sys_p,"Expand query",node_hint="preprocess_query")
    log_llm_call(_A,"preprocess_query_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"expanded_queries":r.get("expansions",[q]),"original_query":q,"status":ExecutionStatus.RUNNING,
            "current_node":"preprocess_query_node",
            "execution_trace":[build_trace_entry("preprocess_query_node",int((time.monotonic()-t0)*1000),llm_tokens=100)]}
