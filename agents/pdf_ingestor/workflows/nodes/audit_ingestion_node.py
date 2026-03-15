"""
agents/pdf_ingestor/workflows/nodes/audit_ingestion_node.py
=============================================================
Node function: ``audit_ingestion_node``

Single-responsibility node — part of the pdf_ingestor LangGraph workflow.
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
from agents.pdf_ingestor.prompts.defaults import get_default_prompt
from agents.pdf_ingestor.tools.pdf_extractor import PDFExtractor, VectorStoreWriter

# ── Module-level constants ────────────────────────────────────────────────────
_A="pdf_ingestor_agent"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k,state,**kw):
    ov=state.get("config",{}).get("prompts",{}).get(k)
    fb=ov or get_default_prompt(f"pdf_{k}")
    return get_prompt(f"pdf_{k}",agent_name=_A,fallback=fb,**kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"pdf_ingestor_{key}")
    return get_prompt(f"pdf_ingestor_{key}", agent_name="pdf_ingestor", fallback=fb, **kw)


def audit_ingestion_node(state):
    t0=time.monotonic()
    sys_p=_p("audit",state,filename=state.get("pdf_path",""),chunk_count=state.get("chunk_count",0),
             page_count=state.get("page_count",0),errors=state.get("upsert_result",{}).get("errors",[]))
    r=call_llm(get_llm(),sys_p,"Audit ingestion",node_hint="audit_ingestion")
    log_llm_call(_A,"audit_ingestion_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    resp=build_agent_response(state,payload={"chunks_created":state.get("chunk_count",0),
        "pages_processed":state.get("page_count",0),"embedding_model":state.get("embedding_model"),
        "upsert_result":state.get("upsert_result",{}),"status":r.get("status","success")},confidence_score=0.95)
    return {"ingestion_summary":r,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"audit_ingestion_node",
            "execution_trace":[build_trace_entry("audit_ingestion_node",int((time.monotonic()-t0)*1000),llm_tokens=120)],
            "audit_events":[make_audit_event(state,"audit_ingestion_node","INGESTION_AUDITED")]}
