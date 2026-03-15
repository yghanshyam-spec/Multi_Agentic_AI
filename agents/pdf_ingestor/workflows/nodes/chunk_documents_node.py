"""
agents/pdf_ingestor/workflows/nodes/chunk_documents_node.py
=============================================================
Node function: ``chunk_documents_node``

Single-responsibility node — part of the pdf_ingestor LangGraph workflow.
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


def chunk_documents_node(state):
    t0=time.monotonic()
    chunk_size=state.get("config",{}).get("chunk_size",500)
    chunks=[]
    for page in state.get("cleaned_pages",[]):
        text=page["text"]
        for i in range(0,max(1,len(text)),chunk_size):
            chunk_text=text[i:i+chunk_size]
            chunks.append({"chunk_id":new_id("chk"),"source":state.get("pdf_path",""),
                           "page":page["page"],"text":chunk_text,
                           "char_hash":hashlib.md5(chunk_text.encode()).hexdigest()[:8]})
    return {"chunks":chunks,"chunk_count":len(chunks),"current_node":"chunk_documents_node",
            "execution_trace":[build_trace_entry("chunk_documents_node",int((time.monotonic()-t0)*1000))]}
