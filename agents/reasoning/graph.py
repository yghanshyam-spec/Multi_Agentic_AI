from __future__ import annotations
"""agents/reasoning/graph.py — Reasoning Agent LangGraph entry-point."""
from shared import (
    ReasoningAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False

from shared import ReasoningAgentState, AgentType
from shared.langfuse_manager import get_tracer
from agents.reasoning.nodes.reasoning_nodes import (
    frame_problem_node, generate_hypotheses_node, call_tool_node,
    evaluate_evidence_node, chain_of_thought_node,
    synthesise_conclusion_node, validate_reasoning_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/reasoning/nodes/ location is preserved for backward compatibility.
from agents.reasoning.workflows.nodes import (
    frame_problem_node, generate_hypotheses_node, call_tool_node, evaluate_evidence_node, chain_of_thought_node, synthesise_conclusion_node, validate_reasoning_node,
)


def run_reasoning_agent(raw_input: str, session_id: str = None, agent_config: dict = None) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.REASONING, session_id=session_id)
    state.update({"framed_problem":None,"hypotheses":[],"evidence_set":[],"reasoning_chain":[],
        "conclusion":None,"reasoning_valid":True,"reasoning_issues":[],"tool_results":[],
        "config": agent_config or {}})
    tracer = get_tracer("reasoning_agent")
    with tracer.trace("reasoning_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **frame_problem_node(state)}
        state = {**state, **generate_hypotheses_node(state)}
        state = {**state, **call_tool_node(state)}
        state = {**state, **evaluate_evidence_node(state)}
        state = {**state, **chain_of_thought_node(state)}
        state = {**state, **synthesise_conclusion_node(state)}
        state = {**state, **validate_reasoning_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("conclusion")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_reasoning_agent", "AGENT_COMPLETED")
    )
    return state
