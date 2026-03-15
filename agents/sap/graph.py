from __future__ import annotations
"""agents/sap/graph.py — SAP Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.sap.nodes.sap_agent_nodes import (
    parse_sap_intent_node,select_bapi_node,call_sap_rfc_node,parse_bapi_return_node,
    handle_sap_exception_node,transform_sap_data_node,summarise_sap_response_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/sap/nodes/ location is preserved for backward compatibility.
from agents.sap.workflows.nodes import (
    parse_sap_intent_node, select_bapi_node, call_sap_rfc_node, parse_bapi_return_node, handle_sap_exception_node, transform_sap_data_node, summarise_sap_response_node,
)


def run_sap_agent(raw_input:str,session_id:str=None,agent_config:dict=None)->dict:
    """Natural language → BAPI selection → RFC call → data transform → business summary.
    Consumer config: sap.host/client/user/password/sysnr (PyRFC params),
    prompts.parse_intent / select_bapi / handle_exception / transform_data / summarise_response.
    """
    state=make_base_state(raw_input,AgentType.SAP,session_id=session_id)
    state.update({"sap_module":None,"sap_operation":None,"bapi_hint":None,"sap_key_fields":{},
        "selected_bapi":None,"bapi_import_params":{},"sap_raw_result":{},"sap_return_table":[],
        "sap_has_error":False,"sap_errors":[],"sap_warnings":[],"sap_exception_diagnosis":{},
        "sap_escalate_human":False,"sap_transformed_data":{},"sap_summary":None,"config":agent_config or {}})
    tracer=get_tracer("sap")
    with tracer.trace("sap_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state={**state,**parse_sap_intent_node(state)}
        state={**state,**select_bapi_node(state)}
        state={**state,**call_sap_rfc_node(state)}
        state={**state,**parse_bapi_return_node(state)}
        if state.get("sap_has_error"): state={**state,**handle_sap_exception_node(state)}
        state={**state,**transform_sap_data_node(state)}
        state={**state,**summarise_sap_response_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("sap_summary")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_sap_agent", "AGENT_COMPLETED")
    )
    return state
