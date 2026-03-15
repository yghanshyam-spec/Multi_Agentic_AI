"""
agents/vector_query/workflows/nodes/update_memory_node.py
===========================================================
Node function: ``update_memory_node``

Single-responsibility node — part of the vector_query LangGraph workflow.
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


def update_memory_node(state):
    t0=time.monotonic()
    history=list(state.get("conversation_history",[]))
    history.append({"query":state.get("original_query",""),"answer":state.get("generated_answer","")})
    resp=build_agent_response(state,payload={"answer":state.get("generated_answer",""),
        "sources":[{"section":c.get("section"),"page":c.get("page"),"score":c.get("score")} for c in state.get("reranked_chunks",[])],
        "faithful":state.get("faithful",True),"unsupported_claims":state.get("unsupported_claims",[])},confidence_score=0.9)
    return {"conversation_history":history,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"update_memory_node",
            "execution_trace":[build_trace_entry("update_memory_node",int((time.monotonic()-t0)*1000))]}
