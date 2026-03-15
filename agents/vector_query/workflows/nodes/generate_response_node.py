"""
agents/vector_query/workflows/nodes/generate_response_node.py
===============================================================
Node function: ``generate_response_node``

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


def generate_response_node(state):
    t0=time.monotonic()
    ctx="\n\n".join(f"[{c.get('section','?')} p.{c.get('page','?')}]: {c.get('text','')}"
                    for c in state.get("reranked_chunks",[]))
    sys_p=_p("generate",state,retrieved_chunks=ctx,user_query=state.get("original_query",""))
    r=call_llm(get_llm(),sys_p,"Generate RAG response",node_hint="generate_response")
    log_llm_call(_A,"generate_response_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    answer=r.get("answer",r.get("raw_response","Based on the retrieved documents: "+ctx[:200]))
    return {"generated_answer":answer,"retrieved_context":ctx,"current_node":"generate_response_node",
            "execution_trace":[build_trace_entry("generate_response_node",int((time.monotonic()-t0)*1000),llm_tokens=500)],
            "audit_events":[make_audit_event(state,"generate_response_node","RAG_RESPONSE_GENERATED")]}
