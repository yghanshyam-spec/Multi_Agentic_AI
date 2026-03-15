"""
agents/pdf_ingestor/workflows/nodes/trigger_ingestion_node.py
===============================================================
Node function: ``trigger_ingestion_node``

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


def trigger_ingestion_node(state):
    t0=time.monotonic()
    pdf_path=state.get("pdf_path",state.get("raw_input","document.pdf"))
    return {"pdf_path":pdf_path,"ingestion_id":new_id("ing"),"status":ExecutionStatus.RUNNING,
            "current_node":"trigger_ingestion_node",
            "execution_trace":[build_trace_entry("trigger_ingestion_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"trigger_ingestion_node",f"INGESTION_STARTED:{pdf_path}")]}
