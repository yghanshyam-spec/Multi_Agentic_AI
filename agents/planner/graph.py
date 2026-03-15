from __future__ import annotations
"""agents/planner/graph.py — Planner Agent LangGraph entry-point."""
from shared import (
    PlannerAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False

from shared import PlannerAgentState, AgentType
from shared.langfuse_manager import get_tracer
from agents.planner.nodes.planner_nodes import (
    analyse_goal_node, decompose_tasks_node, resolve_dependencies_node,
    assign_agents_node, estimate_resources_node, validate_plan_node, serialise_plan_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/planner/nodes/ location is preserved for backward compatibility.
from agents.planner.workflows.nodes import (
    analyse_goal_node, decompose_tasks_node, resolve_dependencies_node, assign_agents_node, estimate_resources_node, validate_plan_node, serialise_plan_node,
)


def build_planner_graph():
    if not _LG: return None
    g = StateGraph(PlannerAgentState)
    for name, fn in [("analyse_goal_node",analyse_goal_node),("decompose_tasks_node",decompose_tasks_node),
        ("resolve_dependencies_node",resolve_dependencies_node),("assign_agents_node",assign_agents_node),
        ("estimate_resources_node",estimate_resources_node),("validate_plan_node",validate_plan_node),
        ("serialise_plan_node",serialise_plan_node)]:
        g.add_node(name, fn)
    g.set_entry_point("analyse_goal_node")
    g.add_edge("analyse_goal_node","decompose_tasks_node"); g.add_edge("decompose_tasks_node","resolve_dependencies_node")
    g.add_edge("resolve_dependencies_node","assign_agents_node"); g.add_edge("assign_agents_node","estimate_resources_node")
    g.add_edge("estimate_resources_node","validate_plan_node"); g.add_edge("validate_plan_node","serialise_plan_node")
    g.add_edge("serialise_plan_node", END)
    return g.compile()

def run_planner_agent(raw_input: str, session_id: str = None, agent_config: dict = None) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.PLANNER, session_id=session_id)
    state.update({"goal_analysis":None,"task_graph":[],"execution_order":[],"agent_assignments":{},
        "resource_estimates":{},"validated_plan":None,"workflow_plan":None,"plan_id":None,
        "config": agent_config or {}})
    tracer = get_tracer("planner_agent")
    with tracer.trace("planner_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **analyse_goal_node(state)}
        state = {**state, **decompose_tasks_node(state)}
        state = {**state, **resolve_dependencies_node(state)}
        state = {**state, **assign_agents_node(state)}
        state = {**state, **estimate_resources_node(state)}
        state = {**state, **validate_plan_node(state)}
        state = {**state, **serialise_plan_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("validated_plan")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_planner_agent", "AGENT_COMPLETED")
    )
    return state
