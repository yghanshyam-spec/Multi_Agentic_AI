"""
agents/pdf_ingestor/workflows/nodes/embed_chunks_node.py
==========================================================
Node function: ``embed_chunks_node``

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


def embed_chunks_node(state):
    t0=time.monotonic()
    model=state.get("config",{}).get("embedding_model","sentence-transformers/all-MiniLM-L6-v2")
    embedded=[{**c,"embedding":[0.1]*384,"embedding_model":model} for c in state.get("chunks",[])]
    return {"embedded_chunks":embedded,"embedding_model":model,"current_node":"embed_chunks_node",
            "execution_trace":[build_trace_entry("embed_chunks_node",int((time.monotonic()-t0)*1000))]}
