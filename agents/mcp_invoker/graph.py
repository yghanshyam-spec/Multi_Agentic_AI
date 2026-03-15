from __future__ import annotations
"""agents/mcp_invoker/graph.py — MCP Invoker Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.mcp_invoker.nodes.mcp_invoker_nodes import (
    load_mcp_registry_node,negotiate_capabilities_node,select_mcp_tool_node,
    marshall_mcp_request_node,dispatch_mcp_call_node,unmarshall_mcp_response_node,handle_mcp_error_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/mcp_invoker/nodes/ location is preserved for backward compatibility.
from agents.mcp_invoker.workflows.nodes import (
    load_mcp_registry_node, negotiate_capabilities_node, select_mcp_tool_node, marshall_mcp_request_node, dispatch_mcp_call_node, unmarshall_mcp_response_node, handle_mcp_error_node,
)


def run_mcp_invoker_agent(raw_input:str,session_id:str=None,agent_config:dict=None)->dict:
    """Invoke any MCP-compatible tool via protocol negotiation.
    Consumer config: mcp.servers (list of server configs), prompts.select_tool / handle_error.
    """
    state=make_base_state(raw_input,AgentType.MCP_INVOKER,session_id=session_id)
    state.update({"mcp_registry":[],"mcp_capabilities":{},"selected_server_id":None,
        "selected_tool":None,"tool_parameters":{},"mcp_request":{},"mcp_raw_response":{},
        "mcp_call_error":None,"tool_output":None,"config":agent_config or {}})
    tracer=get_tracer("mcp_invoker_agent")
    with tracer.trace("mcp_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state={**state,**load_mcp_registry_node(state)}
        state={**state,**negotiate_capabilities_node(state)}
        state={**state,**select_mcp_tool_node(state)}
        state={**state,**marshall_mcp_request_node(state)}
        state={**state,**dispatch_mcp_call_node(state)}
        if state.get("mcp_call_error"):
            state={**state,**handle_mcp_error_node(state)}
        else:
            state={**state,**unmarshall_mcp_response_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("tool_output")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_mcp_invoker_agent", "AGENT_COMPLETED")
    )
    return state
