"""
agents/sql/workflows/nodes/execute_query_node.py
========================================================
Node function: ``execute_query_node``

Single-responsibility node — part of the sql_agent LangGraph workflow.
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


def execute_query_node(state):
    t0=time.monotonic()
    db=DBConnector(state.get("config",{}).get("database",{}))
    result=db.execute(state.get("generated_sql","SELECT 1"))
    return {"query_result":result,"query_error":None,"current_node":"execute_query_node",
            "execution_trace":[build_trace_entry("execute_query_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"execute_query_node",f"SQL_EXECUTED:rows={result.get('row_count')}")]}
