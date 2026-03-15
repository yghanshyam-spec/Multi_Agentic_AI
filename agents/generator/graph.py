from __future__ import annotations
"""agents/generator/graph.py — Generator Agent LangGraph entry-point."""
from shared import (
    GeneratorAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False

from shared import GeneratorAgentState, AgentType
from shared.langfuse_manager import get_tracer

# ── Canonical import path: workflows/nodes/ (one file per node) ─────────────
from agents.generator.workflows.nodes import (
    select_template_node, collect_inputs_node, plan_content_node,
    generate_section_node, review_content_node, refine_content_node,
    assemble_document_node,
)


def run_generator_agent(
    raw_input: str,
    working_memory: dict = None,
    session_id: str = None,
    agent_config: dict = None,
) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.GENERATOR, session_id=session_id)
    state.update({
        "template_id": None,
        "collected_inputs": {},
        "content_outline": None,
        "generated_sections": [],
        "review_result": None,
        "refined_content": None,
        "final_document": None,
        "generation_config": {},
        "working_memory": working_memory or {},
        "config": agent_config or {},
    })
    tracer = get_tracer("generator_agent")
    with tracer.trace("generator_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **select_template_node(state)}
        state = {**state, **collect_inputs_node(state)}
        state = {**state, **plan_content_node(state)}
        state = {**state, **generate_section_node(state)}
        state = {**state, **review_content_node(state)}
        state = {**state, **refine_content_node(state)}
        state = {**state, **assemble_document_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("final_document")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_generator_agent", "AGENT_COMPLETED")
    )
    return state
