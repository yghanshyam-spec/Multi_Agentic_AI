"""
agents/sql/workflows/nodes/generate_sql_node.py
=======================================================
Node function: ``generate_sql_node``

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


def generate_sql_node(state):
    t0=time.monotonic()
    sys_p=_p("generate",state,dialect=state.get("db_dialect","postgresql"),
             schema=str(state.get("db_schema",{})),user_request=state.get("cleaned_request",""))
    r=call_llm(get_llm(),sys_p,"Generate SQL",node_hint="generate_sql")
    log_llm_call(_A,"generate_sql_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(r),state.get("session_id",""), token_usage=get_last_token_usage())
    sql=r.get("sql",r.get("raw_response","SELECT 1"))
    return {"generated_sql":sql,"current_node":"generate_sql_node",
            "execution_trace":[build_trace_entry("generate_sql_node",int((time.monotonic()-t0)*1000),llm_tokens=300)],
            "audit_events":[make_audit_event(state,"generate_sql_node","SQL_GENERATED")]}
