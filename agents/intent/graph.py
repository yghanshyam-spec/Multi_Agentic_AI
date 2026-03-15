from __future__ import annotations
"""agents/intent/graph.py — Intent Agent LangGraph entry-point."""
from shared import (
    IntentAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False

from shared import IntentAgentState, AgentType
from shared.langfuse_manager import get_tracer
from agents.intent.nodes.intent_nodes import (
    normalise_input_node, classify_intent_node, extract_entities_node,
    route_by_confidence_node, request_clarification_node,
    split_multi_intent_node, aggregate_responses_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/intent/nodes/ location is preserved for backward compatibility.
from agents.intent.workflows.nodes import (
    normalise_input_node, classify_intent_node, extract_entities_node, route_by_confidence_node, request_clarification_node, split_multi_intent_node, aggregate_responses_node,
)


def build_intent_graph():
    if not _LG: return None
    g = StateGraph(IntentAgentState)
    g.add_node("normalise_input_node",        normalise_input_node)
    g.add_node("classify_intent_node",        classify_intent_node)
    g.add_node("extract_entities_node",       extract_entities_node)
    g.add_node("route_by_confidence_node",    route_by_confidence_node)
    g.add_node("request_clarification_node",  request_clarification_node)
    g.add_node("split_multi_intent_node",     split_multi_intent_node)
    g.add_node("aggregate_responses_node",    aggregate_responses_node)
    g.set_entry_point("normalise_input_node")
    g.add_edge("normalise_input_node",     "classify_intent_node")
    g.add_edge("classify_intent_node",     "extract_entities_node")
    g.add_edge("extract_entities_node",    "route_by_confidence_node")
    g.add_conditional_edges("route_by_confidence_node",
        lambda s: "request_clarification_node" if s.get("clarification_needed") else "split_multi_intent_node",
        {"request_clarification_node":"request_clarification_node","split_multi_intent_node":"split_multi_intent_node"})
    g.add_edge("request_clarification_node", "split_multi_intent_node")
    g.add_edge("split_multi_intent_node",    "aggregate_responses_node")
    g.add_edge("aggregate_responses_node",   END)
    return g.compile()

def run_intent_agent(raw_input: str, session_id: str = None, agent_config: dict = None) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.INTENT, session_id=session_id)
    state.update({"detected_intents":[],"primary_intent":None,"extracted_entities":{},
        "sub_tasks":[],"routing_decision":None,"clarification_needed":False,
        "clarification_q":None,"aggregated_results":None,"confidence_threshold":0.70,
        "config": agent_config or {}})
    tracer = get_tracer("intent_agent")
    with tracer.trace("intent_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **normalise_input_node(state)}
        state = {**state, **classify_intent_node(state)}
        state = {**state, **extract_entities_node(state)}
        state = {**state, **route_by_confidence_node(state)}
        if state.get("clarification_needed"):
            state = {**state, **request_clarification_node(state)}
        state = {**state, **split_multi_intent_node(state)}
        state = {**state, **aggregate_responses_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("aggregated_results")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_intent_agent", "AGENT_COMPLETED")
    )
    return state
