"""
agents/sql/workflows/nodes/format_output_node.py
========================================================
Node function: ``format_output_node``

Single-responsibility node — part of the sql_agent LangGraph workflow.
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
from agents.sql.prompts.defaults import get_default_prompt
from agents.sql.tools.db_connector import DBConnector

# ── Module-level constants ────────────────────────────────────────────────────
_A = "sql"

# ── Tool instances ────────────────────────────────────────────────────────────
# (none)

# ── Private helpers ────────────────────────────────────────────────────────────
def _p(k, state, **kw):
    ov = state.get("config",{}).get("prompts",{}).get(k)
    fb = ov or get_default_prompt(f"sql_{k}")
    return get_prompt(f"sql_{k}", agent_name=_A, fallback=fb, **kw)

# ── Prompt resolver ───────────────────────────────────────────────────────────
def _p(key, state, **kw):
    fb = state.get("config", {}).get("prompts", {}).get(key) or get_default_prompt(f"sql_{key}")
    return get_prompt(f"sql_{key}", agent_name="sql", fallback=fb, **kw)


def format_output_node(state):
    t0=time.monotonic()
    sys_p=_p("format",state,results=str(state.get("query_result",{})),
             user_request=state.get("cleaned_request",""))
    r=call_llm(get_llm(),sys_p,"Format results",node_hint="format_output")
    log_llm_call(_A,"format_output_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    narrative=r.get("narrative",r.get("raw_response","Query completed successfully."))
    resp=build_agent_response(state,payload={"narrative":narrative,"sql":state.get("generated_sql"),
        "rows":state.get("query_result",{}).get("rows",[]),"row_count":state.get("query_result",{}).get("row_count",0)},
        confidence_score=0.9)
    return {"formatted_output":narrative,"agent_response":dict(resp),"status":ExecutionStatus.COMPLETED,
            "current_node":"format_output_node",
            "execution_trace":[build_trace_entry("format_output_node",int((time.monotonic()-t0)*1000),llm_tokens=250)],
            "audit_events":[make_audit_event(state,"format_output_node","RESULT_FORMATTED")]}
