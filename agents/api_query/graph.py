from __future__ import annotations
"""agents/api_query/graph.py — API Query Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.api_query.nodes.api_query_nodes import (
    load_api_spec_node,select_endpoint_node,build_parameters_node,
    manage_auth_node,execute_request_node,parse_response_node,handle_api_error_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/api_query/nodes/ location is preserved for backward compatibility.
from agents.api_query.workflows.nodes import (
    load_api_spec_node, select_endpoint_node, build_parameters_node, manage_auth_node, execute_request_node, parse_response_node, handle_api_error_node,
)


def run_api_query_agent(raw_input:str,session_id:str=None,agent_config:dict=None)->dict:
    """Dynamic API discovery and invocation from natural language.
    Consumer config: api.spec_url, api.base_url, api.auth.type/key/access_token,
    expected_type, prompts.select_endpoint/build_params/parse_response/handle_error.
    """
    state=make_base_state(raw_input,AgentType.API_QUERY,session_id=session_id)
    state.update({"api_spec":{},"endpoint_catalogue":[],"selected_endpoint":None,"http_method":"GET",
        "parameters_needed":[],"request_params":{},"request_headers":{},"auth_refreshed":False,
        "raw_api_response":{},"api_error":None,"parsed_response":{},"api_error_diagnosis":{},
        "retry_api":False,"extracted_entities":{},"config":agent_config or {}})
    tracer=get_tracer("api_query_agent")
    with tracer.trace("api_query_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state={**state,**load_api_spec_node(state)}
        state={**state,**select_endpoint_node(state)}
        state={**state,**build_parameters_node(state)}
        state={**state,**manage_auth_node(state)}
        state={**state,**execute_request_node(state)}
        if state.get("api_error"): state={**state,**handle_api_error_node(state)}
        else: state={**state,**parse_response_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("parsed_response")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_api_query_agent", "AGENT_COMPLETED")
    )
    return state
