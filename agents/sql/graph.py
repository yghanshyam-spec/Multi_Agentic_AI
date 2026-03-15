from __future__ import annotations
"""agents/sql/graph.py — SQL Agent entry point."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.sql.nodes.sql_agent_nodes import (
    process_input_node, fetch_schema_node, generate_sql_node,
    validate_sql_node, execute_query_node, correct_sql_node, format_output_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/sql/nodes/ location is preserved for backward compatibility.
from agents.sql.workflows.nodes import (
    process_input_node, fetch_schema_node, generate_sql_node, validate_sql_node, execute_query_node, correct_sql_node, format_output_node,
)


def run_sql_agent(raw_input: str, session_id: str = None, agent_config: dict = None) -> dict:
    """Natural language → validated SQL → execution → formatted response.
    Consumer config: database.dialect, database.host, database.credentials,
    prompts.generate / validate / correct / format, max_retries (int).
    """
    state = make_base_state(raw_input, AgentType.SQL, session_id=session_id)
    state.update({"cleaned_request":None,"db_schema":{},"db_dialect":"postgresql",
        "generated_sql":None,"sql_valid":False,"sql_safe":False,"validation_issues":[],
        "query_result":None,"query_error":None,"formatted_output":None,
        "retry_count":0,"config":agent_config or {}})
    tracer = get_tracer("sql")
    with tracer.trace("sql_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state={**state,**process_input_node(state)}
        state={**state,**fetch_schema_node(state)}
        state={**state,**generate_sql_node(state)}
        state={**state,**validate_sql_node(state)}
        if state.get("sql_safe",True):
            state={**state,**execute_query_node(state)}
            if state.get("query_error") and state.get("retry_count",0)<2:
                state={**state,**correct_sql_node(state)}
                state={**state,**execute_query_node(state)}
        state={**state,**format_output_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("formatted_output")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_sql_agent", "AGENT_COMPLETED")
    )
    return state
