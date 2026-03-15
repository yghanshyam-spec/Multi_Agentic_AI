from __future__ import annotations
"""agents/salesforce/graph.py — Salesforce Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.salesforce.nodes.salesforce_nodes import (
    parse_sf_intent_node,generate_soql_node,call_salesforce_api_node,
    validate_sf_records_node,enrich_sf_data_node,format_sf_response_node,log_sf_operation_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/salesforce/nodes/ location is preserved for backward compatibility.
from agents.salesforce.workflows.nodes import (
    parse_sf_intent_node, generate_soql_node, call_salesforce_api_node, validate_sf_records_node, enrich_sf_data_node, format_sf_response_node, log_sf_operation_node,
)


def run_salesforce_agent(raw_input:str,session_id:str=None,agent_config:dict=None)->dict:
    """LLM-driven Salesforce interaction: SOQL generation, DML, enrichment, audit.
    Consumer config: salesforce.instance_url/username/password/security_token,
    enable_enrichment (bool), validation_rules (dict), prompts.*.
    """
    state=make_base_state(raw_input,AgentType.SALESFORCE,session_id=session_id)
    state.update({"sf_operation_type":None,"sf_object":None,"sf_filters":{},"sf_fields":[],
        "soql_query":None,"sf_raw_result":{},"sf_error":None,"sf_records_valid":True,
        "sf_validation_issues":[],"sf_enriched_data":{},"sf_formatted_response":None,
        "sf_audit_entry":{},"config":agent_config or {}})
    tracer=get_tracer("salesforce_agent")
    with tracer.trace("salesforce_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        for fn in [parse_sf_intent_node,generate_soql_node,call_salesforce_api_node,
                   validate_sf_records_node,enrich_sf_data_node,format_sf_response_node,log_sf_operation_node]:
            state={**state,**fn(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("sf_formatted_response")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_salesforce_agent", "AGENT_COMPLETED")
    )
    return state
