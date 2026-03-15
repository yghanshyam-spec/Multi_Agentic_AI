from __future__ import annotations
"""agents/workflow/graph.py — Workflow Agent LangGraph entry-point."""
from shared import (
    WorkflowAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False

from shared import WorkflowAgentState, AgentType
from shared.langfuse_manager import get_tracer
from agents.workflow.nodes.workflow_nodes import (
    load_workflow_definition_node, sequence_steps_node, dispatch_step_node,
    aggregate_step_results_node, evaluate_conditions_node,
    manage_workflow_error_node, summarise_workflow_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/workflow/nodes/ location is preserved for backward compatibility.
from agents.workflow.workflows.nodes import (
    load_workflow_definition_node, sequence_steps_node, dispatch_step_node, aggregate_step_results_node, evaluate_conditions_node, manage_workflow_error_node, summarise_workflow_node,
)


def run_workflow_agent(raw_input: str, workflow_plan: dict = None, session_id: str = None, agent_config: dict = None) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.WORKFLOW, session_id=session_id)
    state.update({"workflow_definition":None,"current_step_index":0,"current_step":None,
        "completed_steps":[],"step_results":{},"workflow_status":"PENDING","condition_results":{},
        "workflow_summary":None,"config":agent_config or {},
        "working_memory":{"workflow_plan":workflow_plan,"tasks":workflow_plan.get("tasks",[]) if workflow_plan else []}})
    tracer = get_tracer("workflow_agent")
    with tracer.trace("workflow_execution", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **load_workflow_definition_node(state)}
        state = {**state, **sequence_steps_node(state)}
        steps = state.get("workflow_definition",{}).get("steps",[])
        for _ in range(len(steps)):
            state = {**state, **dispatch_step_node(state)}
            state = {**state, **evaluate_conditions_node(state)}
        state = {**state, **aggregate_step_results_node(state)}
        state = {**state, **manage_workflow_error_node(state)}
        state = {**state, **summarise_workflow_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("workflow_summary")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_workflow_agent", "AGENT_COMPLETED")
    )
    return state
