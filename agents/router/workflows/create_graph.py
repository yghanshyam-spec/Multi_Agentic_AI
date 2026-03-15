"""
agents/router/workflows/create_graph.py
=========================================
LangGraph graph assembly for the Router agent.

Called by pipeline.py ONCE at startup to compile the graph::

    from agents.router.workflows.create_graph import build_router_graph
    graph = build_router_graph()

The compiled graph is then passed into run_router() in engine.py::

    from agents.router.core.engine import run_router
    result = run_router(raw_input, graph=graph, ...)

Individual node functions live in workflows/nodes/ — one file per node.
The graph is typed against RouterAgentState from shared.state.
Tracing: shared.langfuse_manager only — no local langfuse_client or prompt_manager.
"""
from __future__ import annotations

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    _LG_AVAILABLE = True
except ImportError:
    _LG_AVAILABLE = False

from shared.state import RouterAgentState
from shared.common import get_tracer, get_logger

from agents.router.workflows.nodes import (
    analyse_request_node,
    monitor_load_node,
    plan_routing_node,
    activate_agents_node,
    monitor_execution_node,
    collect_results_node,
    orchestrate_response_node,
)

logger = get_logger(__name__)


def build_router_graph():
    """
    Assemble and compile the Router LangGraph workflow.

    Returns a compiled StateGraph[RouterAgentState], or None if LangGraph
    is not installed (engine.py will fall back to imperative node execution).

    Graph topology (linear — no conditional edges):
        analyse_request_node
            → monitor_load_node
            → plan_routing_node
            → activate_agents_node
            → monitor_execution_node
            → collect_results_node
            → orchestrate_response_node
            → END
    """
    if not _LG_AVAILABLE:
        logger.warning("[build_router_graph] langgraph not installed — returning None.")
        return None

    graph = StateGraph(RouterAgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("analyse_request_node",      analyse_request_node)
    graph.add_node("monitor_load_node",         monitor_load_node)
    graph.add_node("plan_routing_node",         plan_routing_node)
    graph.add_node("activate_agents_node",      activate_agents_node)
    graph.add_node("monitor_execution_node",    monitor_execution_node)
    graph.add_node("collect_results_node",      collect_results_node)
    graph.add_node("orchestrate_response_node", orchestrate_response_node)

    # ── Wire edges ────────────────────────────────────────────────────────────
    graph.set_entry_point("analyse_request_node")
    graph.add_edge("analyse_request_node",      "monitor_load_node")
    graph.add_edge("monitor_load_node",         "plan_routing_node")
    graph.add_edge("plan_routing_node",         "activate_agents_node")
    graph.add_edge("activate_agents_node",      "monitor_execution_node")
    graph.add_edge("monitor_execution_node",    "collect_results_node")
    graph.add_edge("collect_results_node",      "orchestrate_response_node")
    graph.add_edge("orchestrate_response_node", END)

    compiled = graph.compile(checkpointer=MemorySaver())
    logger.info("[build_router_graph] Router graph compiled (7 nodes).")
    return compiled
