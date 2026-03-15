"""
agents/pdf_ingestor/workflows/nodes/upsert_vectors_node.py
============================================================
Node function: ``upsert_vectors_node``

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


def upsert_vectors_node(state):
    t0=time.monotonic()
    writer=VectorStoreWriter(state.get("config",{}).get("vector_store",{}))
    result=writer.upsert(state.get("embedded_chunks",[]))
    return {"upsert_result":result,"current_node":"upsert_vectors_node",
            "execution_trace":[build_trace_entry("upsert_vectors_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"upsert_vectors_node",
                f"VECTORS_UPSERTED:{result.get('upserted')}")]}
